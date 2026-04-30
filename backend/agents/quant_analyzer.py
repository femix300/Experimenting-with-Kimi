"""
Agent 02: Quantitative Analysis Agent (Firestore Refactored)
============================================================
Original: agents/quant_analyzer.py

Changes made:
- Added Firestore sync for quant metrics
- Replaced SQLite-only writes with dual writes (SQLite + Firestore)
- Ensures quant metrics are available in Firestore for signal generator
"""

from services.bayse_client import bayse_client, BayseAPIError
from utils.calculations import (
    calculate_momentum,
    get_momentum_direction,
    calculate_volume_acceleration,
    get_volume_trend,
    calculate_bid_ask_spread,
    get_order_book_bias
)
from decimal import Decimal
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def _get_market_model():
    """Lazy import to avoid Django setup issues"""
    from markets.models import Market
    return Market


def _get_quant_metrics_model():
    """Lazy import to avoid Django setup issues"""
    from markets.models import QuantMetrics
    return QuantMetrics


def _get_price_history_model():
    """Lazy import to avoid Django setup issues"""
    from markets.models import PriceHistory
    return PriceHistory


def analyze_market(market_id):
    """
    Perform complete quantitative analysis on a market

    Args:
        market_id: Database ID of the Market object

    Returns:
        Dictionary with all quant metrics
    """
    try:
        # Get market from database
        Market = _get_market_model()
        market = Market.objects.get(bayse_event_id=market_id)
        logger.info(f"Analyzing market: {market.title}")

        # Fetch all required data from Bayse
        price_history = fetch_price_history(market)
        ticker_data = fetch_ticker_data(market)
        order_book_data = fetch_order_book(market)

        # Calculate momentum metrics
        momentum_metrics = calculate_momentum_metrics(price_history)

        # Calculate volume metrics
        volume_metrics = calculate_volume_metrics(price_history, ticker_data)

        # Calculate order book metrics
        order_book_metrics = calculate_order_book_metrics(order_book_data)

        # Combine all metrics
        quant_metrics = {
            **momentum_metrics,
            **volume_metrics,
            **order_book_metrics,
        }

        # Store metrics in SQLite database
        save_quant_metrics(market, quant_metrics)

        # --- NEW: Sync to Firestore for Agent 04 ---
        sync_quant_metrics_to_firestore(market, quant_metrics)

        logger.info(f"Analysis complete for {market.title}")
        logger.info(
            f"  Momentum: {quant_metrics['momentum_score']} ({quant_metrics['momentum_direction']})")
        logger.info(
            f"  Volume Acceleration: {quant_metrics['volume_acceleration']}")
        logger.info(f"  Order Book Bias: {quant_metrics['order_book_bias']}")

        return quant_metrics

    except Market.DoesNotExist:
        logger.error(f"Market with ID {market_id} not found")
        raise ValueError(f"Market {market_id} not found")
    except Exception as e:
        logger.error(f"Error analyzing market {market_id}: {str(e)}")
        raise


def sync_quant_metrics_to_firestore(market, quant_metrics):
    """
    Sync quantitative metrics to Firestore for real-time access.
    """
    try:
        from utils.firebase_client import fs, Collection
        
        # Use bayse_event_id as the document ID for consistency
        firestore_doc_id = market.bayse_event_id
        
        quant_doc = {
            "market_id": firestore_doc_id,
            "market_title": market.title,
            "momentum_score": float(quant_metrics.get('momentum_score', 0)),
            "momentum_direction": quant_metrics.get('momentum_direction', 'neutral'),
            "price_change_1h": float(quant_metrics.get('price_change_1h', 0)),
            "price_change_6h": float(quant_metrics.get('price_change_6h', 0)),
            "price_change_24h": float(quant_metrics.get('price_change_24h', 0)),
            "volume_acceleration": float(quant_metrics.get('volume_acceleration', 1.0)),
            "volume_trend": quant_metrics.get('volume_trend', 'stable'),
            "bid_ask_spread": float(quant_metrics.get('bid_ask_spread', 0)),
            "order_book_bias": quant_metrics.get('order_book_bias', 'neutral'),
            "bid_depth": float(quant_metrics.get('bid_depth', 0)),
            "ask_depth": float(quant_metrics.get('ask_depth', 0)),
            "calculated_at": timezone.now(),
        }
        
        fs.set(Collection.QUANT_METRICS, firestore_doc_id, quant_doc, merge=True)
        logger.info(f"Synced quant metrics to Firestore for market {market.bayse_event_id}")
        
    except Exception as e:
        logger.error(f"Failed to sync quant metrics to Firestore: {e}")


def fetch_price_history(market, hours=24, interval='1h'):
    """
    Fetch and store price history from Bayse
    """
    try:
        # Map hours to timePeriod
        if hours <= 12:
            time_period = '12H'
        elif hours <= 24:
            time_period = '24H'
        elif hours <= 168:
            time_period = '1W'
        elif hours <= 720:
            time_period = '1M'
        else:
            time_period = '1Y'
        
        # Fetch from Bayse API
        history_data = bayse_client.get_price_history(
            event_id=market.bayse_event_id,
            outcome='YES',
            time_period=time_period,
            market_id=market.bayse_market_id
        )

        if not history_data:
            logger.warning(f"No price history returned for {market.title}")
            return []

        # Store in database
        PriceHistory = _get_price_history_model()
        for point in history_data:
            try:
                timestamp = parse_timestamp(point.get('timestamp'))
                if not timestamp:
                    continue

                PriceHistory.objects.update_or_create(
                    market=market,
                    timestamp=timestamp,
                    defaults={
                        'price': Decimal(str(point.get('price', 0))),
                        'volume': Decimal(str(point.get('volume', 0))),
                    }
                )
            except Exception as e:
                logger.error(f"Error storing price point: {str(e)}")
                continue

        return history_data

    except BayseAPIError as e:
        logger.error(f"Bayse API error fetching price history: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error fetching price history: {str(e)}")
        return []


def fetch_ticker_data(market):
    """
    Fetch current ticker data from Bayse
    """
    try:
        if not market.bayse_market_id:
            logger.warning(f"No market ID for {market.title}")
            return {}

        ticker = bayse_client.get_ticker(
            market_id=market.bayse_market_id,
            outcome='YES'
        )

        # Update market with latest price
        if ticker:
            last_price = ticker.get('lastPrice')
            volume_24h = ticker.get('volume24h')
            
            if last_price:
                market.current_price = Decimal(str(last_price))
            if volume_24h:
                market.volume_24h = Decimal(str(volume_24h))
            market.save()

        return ticker or {}

    except BayseAPIError as e:
        logger.error(f"Bayse API error fetching ticker: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Error fetching ticker: {str(e)}")
        return {}


def fetch_order_book(market, depth=10):
    """
    Fetch order book data from Bayse
    """
    try:
        # First, get the outcome_id
        outcome_id = bayse_client.get_outcome_id(market.bayse_event_id, outcome_label='YES')
        
        if not outcome_id:
            logger.warning(f"No outcome_id found for market {market.id}")
            return {}

        # Get order book with outcome_id
        order_book = bayse_client.get_order_book(
            outcome_id=outcome_id,
            depth=depth,
            currency='USD'
        )

        return order_book or {}

    except BayseAPIError as e:
        logger.error(f"Bayse API error fetching order book: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Error fetching order book: {str(e)}")
        return {}


def calculate_momentum_metrics(price_history):
    """
    Calculate momentum metrics from price history

    Args:
        price_history: List of price data points

    Returns:
        Dictionary with momentum metrics
    """
    if not price_history:
        return {
            'momentum_score': 0,
            'momentum_direction': 'neutral',
            'price_change_1h': 0,
            'price_change_6h': 0,
            'price_change_24h': 0,
        }

    try:
        # Extract prices (last 24 points for momentum calculation)
        prices = [float(point.get('price', 0))
                  for point in price_history[-24:]]

        # Calculate momentum score
        momentum_score = calculate_momentum(prices, normalize=True)
        momentum_direction = get_momentum_direction(momentum_score)

        # Calculate price changes at different intervals
        current_price = prices[-1] if prices else 0

        price_change_1h = calculate_price_change(prices, -1, current_price)
        price_change_6h = calculate_price_change(prices, -6, current_price)
        price_change_24h = calculate_price_change(prices, -24, current_price)

        return {
            'momentum_score': momentum_score,
            'momentum_direction': momentum_direction,
            'price_change_1h': price_change_1h,
            'price_change_6h': price_change_6h,
            'price_change_24h': price_change_24h,
        }

    except Exception as e:
        logger.error(f"Error calculating momentum metrics: {str(e)}")
        return {
            'momentum_score': 0,
            'momentum_direction': 'neutral',
            'price_change_1h': 0,
            'price_change_6h': 0,
            'price_change_24h': 0,
        }


def calculate_price_change(prices, lookback_index, current_price):
    """
    Calculate price change from a lookback point

    Args:
        prices: List of prices
        lookback_index: Index to look back to (negative)
        current_price: Current price

    Returns:
        Price change as decimal
    """
    try:
        if len(prices) < abs(lookback_index):
            return 0

        old_price = prices[lookback_index]
        if old_price == 0:
            return 0

        change = ((current_price - old_price) / old_price)
        return round(change, 6)

    except Exception as e:
        logger.error(f"Error calculating price change: {str(e)}")
        return 0


def calculate_volume_metrics(price_history, ticker_data):
    """
    Calculate volume metrics

    Args:
        price_history: List of price data points
        ticker_data: Current ticker data

    Returns:
        Dictionary with volume metrics
    """
    if not price_history:
        return {
            'volume_acceleration': 1.0,
            'volume_trend': 'stable',
        }

    try:
        # Calculate volume acceleration (last 3h vs previous 3h)
        volumes = [float(point.get('volume', 0)) for point in price_history]

        if len(volumes) >= 6:
            recent_volume = sum(volumes[-3:])  # Last 3 hours
            previous_volume = sum(volumes[-6:-3])  # Previous 3 hours
        else:
            recent_volume = sum(volumes)
            previous_volume = recent_volume

        volume_acceleration = calculate_volume_acceleration(
            recent_volume, previous_volume)
        volume_trend = get_volume_trend(volume_acceleration)

        return {
            'volume_acceleration': volume_acceleration,
            'volume_trend': volume_trend,
        }

    except Exception as e:
        logger.error(f"Error calculating volume metrics: {str(e)}")
        return {
            'volume_acceleration': 1.0,
            'volume_trend': 'stable',
        }


def calculate_order_book_metrics(order_book_data):
    """
    Calculate order book metrics

    Args:
        order_book_data: Order book data from Bayse

    Returns:
        Dictionary with order book metrics
    """
    if not order_book_data:
        return {
            'bid_ask_spread': 0,
            'order_book_bias': 'neutral',
            'bid_depth': 0,
            'ask_depth': 0,
        }

    try:
        bids = order_book_data.get('bids', [])
        asks = order_book_data.get('asks', [])

        # Calculate best bid and ask
        best_bid = float(bids[0]['price']) if bids else 0
        best_ask = float(asks[0]['price']) if asks else 0

        # Calculate spread
        spread = calculate_bid_ask_spread(best_bid, best_ask)

        # Calculate total depth on each side
        bid_depth = sum(float(bid.get('quantity', 0)) for bid in bids)
        ask_depth = sum(float(ask.get('quantity', 0)) for ask in asks)

        # Determine order book bias
        order_book_bias = get_order_book_bias(bid_depth, ask_depth)

        return {
            'bid_ask_spread': spread,
            'order_book_bias': order_book_bias,
            'bid_depth': Decimal(str(bid_depth)),
            'ask_depth': Decimal(str(ask_depth)),
        }

    except Exception as e:
        logger.error(f"Error calculating order book metrics: {str(e)}")
        return {
            'bid_ask_spread': 0,
            'order_book_bias': 'neutral',
            'bid_depth': 0,
            'ask_depth': 0,
        }


def save_quant_metrics(market, metrics):
    """
    Save quant metrics to SQLite database

    Args:
        market: Market object
        metrics: Dictionary of calculated metrics
    """
    try:
        QuantMetrics = _get_quant_metrics_model()
        QuantMetrics.objects.create(
            market=market,
            momentum_score=Decimal(str(metrics['momentum_score'])),
            momentum_direction=metrics['momentum_direction'],
            price_change_1h=Decimal(str(metrics['price_change_1h'])),
            price_change_6h=Decimal(str(metrics['price_change_6h'])),
            price_change_24h=Decimal(str(metrics['price_change_24h'])),
            volume_acceleration=Decimal(str(metrics['volume_acceleration'])),
            volume_trend=metrics['volume_trend'],
            bid_ask_spread=Decimal(str(metrics['bid_ask_spread'])),
            order_book_bias=metrics['order_book_bias'],
            bid_depth=metrics.get('bid_depth', 0),
            ask_depth=metrics.get('ask_depth', 0),
        )
        logger.info(f"Saved quant metrics for {market.title}")
    except Exception as e:
        logger.error(f"Error saving quant metrics: {str(e)}")


def get_latest_quant_metrics(market):
    """
    Get the most recent quant metrics for a market

    Args:
        market: Market object

    Returns:
        QuantMetrics object or None
    """
    try:
        return market.quant_metrics.latest()
    except _get_quant_metrics_model().DoesNotExist:
        return None


from django.utils import timezone as django_timezone

def parse_timestamp(timestamp_value):
    if not timestamp_value:
        return None
    try:
        if isinstance(timestamp_value, (int, float)):
            from datetime import datetime
            naive_dt = datetime.fromtimestamp(timestamp_value / 1000)
            return django_timezone.make_aware(naive_dt)
        if isinstance(timestamp_value, str):
            from dateutil import parser
            naive_dt = parser.parse(timestamp_value)
            return django_timezone.make_aware(naive_dt) if not django_timezone.is_aware(naive_dt) else naive_dt
        return None
    except Exception as e:
        logger.error(f"Error parsing timestamp '{timestamp_value}': {e}")
        return None