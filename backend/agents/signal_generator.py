"""
Agent 04: Signal Generator (Firestore Refactored)
==================================================
Original: agents/signal_generator.py

This is the orchestrator agent that ties together outputs from Agents 01-03
and produces the final Signal document.

Changes made:
- Replaced Signal.objects.create()  ->  fs.set(Collection.SIGNALS, ...)
- Reads market, quant_metrics, ai_analysis from Firestore instead of ORM.
- signal_doc_id is deterministic: {market_event_id}_signal for single active signal per market.
- Returns dict (not ORM object).
- Uses original field names (probability, confidence, reasoning, sources) for frontend compatibility.
"""

from utils.firebase_client import fs, Collection
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def generate_signal(market_event_id: str, user_bankroll: float = 10000) -> dict:
    """
    Generate a complete trading signal for a market.

    Pipeline:
        1. Fetch market from Firestore
        2. Fetch latest quant_metrics from Firestore
        3. Fetch latest AI analysis from Firestore
        4. Calculate edge + Kelly criterion
        5. Write signal to Firestore

    Args:
        market_event_id: Firestore doc ID of the market

    Returns:
        Signal dict (the Firestore document).
    """
    from django.utils import timezone

    # 1. Fetch market
    market = fs.get(Collection.MARKETS, market_event_id)
    if not market:
        raise ValueError(f"Market {market_event_id} not found")

    # 2. Fetch quant metrics
    quant = fs.get(Collection.QUANT_METRICS, market_event_id) or {}

    # 3. Fetch AI analysis (using original field names)
    ai_results = fs.query(
        Collection.AI_ANALYSES,
        filters=[("market_id", "==", market_event_id)],
        order_by=("analyzed_at", True),
        limit=1,
    )
    ai = ai_results[0] if ai_results else {}

    # After getting ai, add this line:
    model_used = ai.get("model_used", "unknown")

    # Debug logging
    if ai:
        logger.info(f"Found AI analysis: probability={ai.get('probability')}, confidence={ai.get('confidence')}")
    else:
        logger.warning(f"No AI analysis found for market {market_event_id}")

    # 4. Calculate signal parameters using original field names
    current_price = Decimal(str(market.get("current_price", 0)))
    implied_prob = Decimal(str(market.get("implied_probability", 50)))
    
    # Use original field names from Firestore
    ai_prob = Decimal(str(ai.get("probability", implied_prob)))
    confidence = int(ai.get("confidence", 50))
    reasoning = ai.get("reasoning", "")
    sources = ai.get("sources", "")

    # Edge = AI probability - market implied probability
    edge = ai_prob - implied_prob

    # Expected value per naira staked
    if edge > 0 and current_price > 0:
        ev = (ai_prob / 100) * (1 / current_price) - 1
    elif edge < 0 and current_price > 0:
        ev = ((100 - ai_prob) / 100) * (1 / (1 - current_price)) - 1
    else:
        ev = Decimal("0")

    # Kelly Criterion: f* = (bp - q) / b
    bankroll = Decimal(str(user_bankroll))
    if current_price > 0 and edge != 0:
        b = (1 / current_price) - 1
        p = ai_prob / 100
        q = 1 - p
        kelly_f = (b * p - q) / b if b != 0 else Decimal("0")
        kelly_f = max(Decimal("0"), min(Decimal("1"), kelly_f))
        kelly_pct = kelly_f * 100
        rec_conservative = bankroll * kelly_f * Decimal("0.25")
        rec_balanced = bankroll * kelly_f * Decimal("0.50")
        rec_aggressive = bankroll * kelly_f * Decimal("1.0")
    else:
        kelly_f = Decimal("0")
        kelly_pct = Decimal("0")
        rec_conservative = rec_balanced = rec_aggressive = Decimal("0")

    # Direction
    abs_edge = abs(float(edge))
    if edge > 0 and abs_edge >= 5:
        direction = "BUY"
    elif edge < 0 and abs_edge >= 5:
        direction = "SELL"
    else:
        direction = "WAIT"

    # Signal strength
    if abs_edge >= 25:
        strength = "strong"
    elif abs_edge >= 15:
        strength = "moderate"
    else:
        strength = "weak"

    # Confidence level
    if confidence >= 70:
        conf_level = "high"
    elif confidence >= 40:
        conf_level = "medium"
    else:
        conf_level = "low"

    # 5. Archive any existing active signal for this market
    _archive_existing_signal(market_event_id)

    # 6. Write new signal to Firestore
    now = timezone.now()
    signal_doc_id = f"{market_event_id}_signal"
    signal_doc = {
        "market_id": market_event_id,
        "market_title": market.get("title", ""),
        "market_event_id": market.get("bayse_event_id", ""),
        "direction": direction,
        "edge_score": float(edge.quantize(Decimal("0.01"))),
        "expected_value": float(ev.quantize(Decimal("0.000001"))),
        "market_probability": float(implied_prob.quantize(Decimal("0.01"))),
        "ai_probability": float(ai_prob.quantize(Decimal("0.01"))),
        "model_used": model_used,  # Add this to signal_doc
        "confidence": confidence,
        "confidence_level": conf_level,
        "kelly_percentage": float(kelly_pct.quantize(Decimal("0.01"))),
        "recommended_stake_conservative": float(rec_conservative.quantize(Decimal("0.01"))),
        "recommended_stake_balanced": float(rec_balanced.quantize(Decimal("0.01"))),
        "recommended_stake_aggressive": float(rec_aggressive.quantize(Decimal("0.01"))),
        "reasoning": reasoning,
        "news_context": sources,
        "is_active": True,
        "signal_strength": strength,
        "created_at": now,
        "expires_at": market.get("closes_at"),
        "quant_snapshot": {
            "momentum_score": quant.get("momentum_score"),
            "momentum_direction": quant.get("momentum_direction"),
            "volume_acceleration": quant.get("volume_acceleration"),
            "order_book_bias": quant.get("order_book_bias"),
        },
    }

    fs.set(Collection.SIGNALS, signal_doc_id, signal_doc)
    logger.info(f"Signal generated: {market.get('title')} | {direction} | Edge: {float(edge):.1f}% | Kelly: {float(kelly_pct):.1f}%")

    return signal_doc


def _archive_existing_signal(market_event_id: str):
    """
    Move the current active signal to a history subcollection before overwriting.
    This preserves signal lineage without accumulating endless top-level docs.
    """
    from django.utils import timezone
    
    old = fs.get(Collection.SIGNALS, f"{market_event_id}_signal")
    if old:
        old["archived_at"] = timezone.now()
        old["is_active"] = False
        archive_id = f"{market_event_id}_{old.get('created_at', 'unknown')}"
        fs.set_subdoc(
            parent_collection=Collection.SIGNALS,
            parent_id=f"{market_event_id}_signal",
            sub_collection="history",
            subdoc_id=archive_id,
            data=old,
        )
        logger.info(f"Archived old signal for market {market_event_id}")


def get_active_signals(limit=20, min_edge=15) -> list[dict]:
    """
    Get active signals from Firestore (replaces ORM query).
    """
    filters = [("is_active", "==", True)]
    if min_edge:
        filters.append(("edge_score", ">=", min_edge))

    return fs.query(
        collection=Collection.SIGNALS,
        filters=filters,
        order_by=("edge_score", True),
        limit=limit,
    )


def deactivate_expired_signals() -> int:
    """
    Deactivate signals whose expires_at has passed.
    Returns count deactivated.
    """
    from django.utils import timezone
    from dateutil import parser
    
    now = timezone.now()
    count = 0
    
    # Get all active signals from Firestore
    active_signals = fs.query(
        Collection.SIGNALS,
        filters=[("is_active", "==", True)],
    )
    
    for signal_doc in active_signals:
        expires_at = signal_doc.get("expires_at")
        
        if not expires_at:
            continue
        
        # Convert string to datetime if needed (Firestore stores as string sometimes)
        if isinstance(expires_at, str):
            try:
                expires_at = parser.parse(expires_at)
            except Exception as e:
                logger.warning(f"Could not parse expires_at: {expires_at}")
                continue
        
        # Make timezone-aware if naive
        if timezone.is_naive(expires_at):
            expires_at = timezone.make_aware(expires_at)
        
        if expires_at <= now:
            signal_doc["is_active"] = False
            signal_doc["deactivated_at"] = now
            doc_id = signal_doc.get("id")
            if not doc_id:
                doc_id = f"{signal_doc.get('market_id')}_signal"
            fs.set(Collection.SIGNALS, doc_id, signal_doc)
            count += 1
            logger.info(f"Deactivated expired signal for market: {signal_doc.get('market_title')}")
    
    logger.info(f"Deactivated {count} expired signals in Firestore")
    return count