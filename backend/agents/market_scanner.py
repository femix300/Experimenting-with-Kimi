"""
Agent 01: Market Scanner (Firestore Refactored)
================================================
Original: agents/market_scanner.py

Changes made:
- Replaced Market.objects.update_or_create()  ->  fs.set(Collection.MARKETS, ...)
- Replaced Market.objects.filter().order_by()  ->  fs.query(Collection.MARKETS, ...)
- Kept all Bayse API logic, scoring, filtering unchanged.
- scan_markets() now returns list of market DICTS (not ORM objects).
- Added bulk sync for batch writes to Firestore.
"""

from services.bayse_client import bayse_client, BayseAPIError
from django.utils import timezone
from decimal import Decimal
from dateutil import parser
from utils.firebase_client import fs, Collection
import logging

logger = logging.getLogger(__name__)


def bulk_sync_markets_to_firestore(markets_data: list) -> bool:
    """
    Push multiple markets to Firestore in a single batch operation.
    """
    if not markets_data:
        return True
    
    # Deduplicate by bayse_event_id before batch write
    unique_markets = {}
    for market in markets_data:
        doc_id = market['bayse_event_id']
        if doc_id not in unique_markets:
            unique_markets[doc_id] = market
    
    if len(unique_markets) != len(markets_data):
        logger.warning(f"Deduplicated {len(markets_data) - len(unique_markets)} duplicate markets")
    
    return fs.batch_set(Collection.MARKETS, unique_markets, merge=True)


def scan_markets(status='open', min_volume=0, min_liquidity=0, max_results=20):
    """
    Scan Bayse for active markets and push directly to Firestore.

    Returns:
        List of market dicts (Firestore documents), ranked by signal_potential_score.
    """
    try:
        logger.info("=" * 70)
        logger.info("STARTING MARKET SCAN")
        logger.info(f"  Status: {status} | Min Volume: {min_volume} | Min Liquidity: {min_liquidity}")
        logger.info("=" * 70)

        response = bayse_client.get_all_events(status=status, size=50)
        if not response:
            logger.warning("No data returned from Bayse API")
            return []

        events = response.get('events', [])
        if not events:
            logger.warning("Events array is empty")
            return []

        markets_saved = []
        skipped = 0
        
        # Collect markets in a list first, then batch write
        markets_to_sync = []

        for idx, event in enumerate(events, 1):
            try:
                event_id = str(event.get('id'))
                title = event.get('title', 'Untitled Event')
                description = event.get('description', '')
                category = map_category(event.get('category', 'other'))

                total_volume = Decimal(str(event.get('totalVolume', 0)))
                liquidity = Decimal(str(event.get('liquidity', 0)))

                # --- Filters (unchanged logic) ---
                if total_volume < min_volume:
                    skipped += 1
                    continue
                if liquidity < min_liquidity:
                    skipped += 1
                    continue

                markets_data = event.get('markets', [])
                if not markets_data:
                    skipped += 1
                    continue

                market_data = markets_data[0]
                market_id = str(market_data.get('id', ''))
                current_price = Decimal(str(market_data.get('outcome1Price', 0.5)))

                closes_at = parse_timestamp(event.get('closingDate'))
                resolved_at = parse_timestamp(event.get('resolutionDate'))
                opens_at = parse_timestamp(event.get('openingDate'))

                implied_prob = bayse_client.calculate_implied_probability(current_price)
                signal_score = calculate_signal_potential(total_volume, liquidity, closes_at)

                # --- Create market document (don't write to Firestore yet) ---
                market_doc = {
                    "bayse_event_id": event_id,
                    "bayse_market_id": market_id,
                    "title": title,
                    "description": description,
                    "category": category,
                    "current_price": float(current_price),
                    "implied_probability": implied_prob,
                    "volume_24h": 0,
                    "total_volume": float(total_volume),
                    "liquidity": float(liquidity),
                    "status": status or event.get('status', 'open'),
                    "opens_at": opens_at.isoformat() if opens_at else None,
                    "closes_at": closes_at.isoformat() if closes_at else None,
                    "resolved_at": resolved_at.isoformat() if resolved_at else None,
                    "signal_potential_score": signal_score,
                    "last_scanned_at": timezone.now().isoformat(),
                    "created_at": timezone.now().isoformat(),
                }

                # Add to batch list instead of writing immediately
                markets_to_sync.append(market_doc)
                logger.info(f"  [QUEUED] {title} (score: {signal_score})")
                
            except Exception as e:
                logger.error(f"Error processing event {event.get('id', 'unknown')}: {e}")
                skipped += 1
                continue

        # Batch write all markets at once
        if markets_to_sync:
            success = bulk_sync_markets_to_firestore(markets_to_sync)
            if success:
                markets_saved = markets_to_sync
                logger.info(f"Batch sync complete: {len(markets_saved)} markets saved")
            else:
                logger.error("Batch sync failed")

        logger.info(f"Scan complete: {len(markets_saved)} saved, {skipped} skipped")

        # --- Query Firestore for top markets (replaces ORM query) ---
        top_markets = fs.query(
            collection=Collection.MARKETS,
            filters=[("status", "in", ["open", "active"])],
            order_by=("signal_potential_score", True),  # descending
            limit=max_results,
        )
        return top_markets

    except BayseAPIError as e:
        logger.error(f"Bayse API error: {e}")
        return []
    except Exception as e:
        logger.exception(f"Unexpected error during scan: {e}")
        return []


def calculate_signal_potential(volume, liquidity, closes_at):
    """Calculate signal potential score for ranking markets."""
    score = 0
    volume_score = min(40, float(volume) / 5000)
    score += volume_score
    liquidity_score = min(30, float(liquidity) / 2000)
    score += liquidity_score

    if closes_at:
        time_remaining_hours = (closes_at - timezone.now()).total_seconds() / 3600
        if 24 <= time_remaining_hours <= 168:
            time_score = 30
        elif time_remaining_hours > 168:
            time_score = 20
        elif time_remaining_hours > 0:
            time_score = max(0, time_remaining_hours / 24 * 30)
        else:
            time_score = 0
        score += time_score

    return round(score, 2)


def map_category(bayse_category):
    """Map Bayse categories to internal categories."""
    if not bayse_category:
        return 'other'
    category_lower = str(bayse_category).lower()
    category_map = {
        'crypto': 'crypto',
        'cryptocurrency': 'crypto',
        'sports': 'sports',
        'football': 'sports',
        'soccer': 'sports',
        'politics': 'politics',
        'entertainment': 'entertainment',
    }
    return category_map.get(category_lower, 'other')


def parse_timestamp(timestamp_str):
    """Parse ISO 8601 timestamp string to datetime object."""
    if not timestamp_str:
        return None
    try:
        return parser.parse(timestamp_str)
    except Exception as e:
        logger.error(f"Error parsing timestamp '{timestamp_str}': {e}")
        return None


def get_top_markets(limit=20, category=None):
    """
    Get top markets from Firestore (replaces ORM query).
    Returns list of dicts.
    """
    filters = [("status", "in", ["open", "active"])]
    if category:
        filters.append(("category", "==", category))

    return fs.query(
        collection=Collection.MARKETS,
        filters=filters,
        order_by=("signal_potential_score", True),
        limit=limit,
    )