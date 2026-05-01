"""
Agent 02: Quantitative Analysis Agent (Firestore-only)
======================================================
No SQLite dependency — reads/writes directly to Firestore.
"""
from services.bayse_client import bayse_client, BayseAPIError
from utils.calculations import (
    calculate_momentum, get_momentum_direction,
    calculate_volume_acceleration, get_volume_trend,
    calculate_bid_ask_spread, get_order_book_bias,
)
from utils.firebase_client import fs, Collection
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def analyze_market(market_id):
    """
    Full quantitative analysis on a market, using Firestore.
    
    Args:
        market_id: bayse_event_id (UUID string)
    Returns:
        dict of quant metrics
    """
    try:
        # Get market from Firestore (not SQLite)
        market = fs.get(Collection.MARKETS, market_id)
        if not market:
            raise ValueError(f"Market {market_id} not found in Firestore")

        title = market.get('title', 'Unknown')
        bayse_market_id = market.get('bayse_market_id', '')
        logger.info(f"Analyzing market: {title}")

        # Fetch data from Bayse
        price_history = fetch_price_history(market_id, bayse_market_id, title)
        ticker_data = fetch_ticker_data(market_id, bayse_market_id, title)
        order_book_data = fetch_order_book(market_id)

        # Calculate metrics
        momentum_metrics = calculate_momentum_metrics(price_history)
        volume_metrics = calculate_volume_metrics(price_history, ticker_data)
        order_book_metrics = calculate_order_book_metrics(order_book_data)

        quant_metrics = {**momentum_metrics, **volume_metrics, **order_book_metrics}

        # Save to Firestore
        save_quant_metrics_to_firestore(market_id, title, quant_metrics)

        logger.info(f"Analysis complete for {title}")
        logger.info(f"  Momentum: {quant_metrics['momentum_score']} ({quant_metrics['momentum_direction']})")

        return quant_metrics

    except Exception as e:
        logger.error(f"Error analyzing market {market_id}: {e}")
        raise


def save_quant_metrics_to_firestore(market_id, title, metrics):
    """Write quant metrics to Firestore (replaces both SQLite writes)."""
    doc = {
        "market_id": market_id,
        "market_title": title,
        "momentum_score": float(metrics.get('momentum_score', 0)),
        "momentum_direction": metrics.get('momentum_direction', 'neutral'),
        "price_change_1h": float(metrics.get('price_change_1h', 0)),
        "price_change_6h": float(metrics.get('price_change_6h', 0)),
        "price_change_24h": float(metrics.get('price_change_24h', 0)),
        "volume_acceleration": float(metrics.get('volume_acceleration', 1.0)),
        "volume_trend": metrics.get('volume_trend', 'stable'),
        "bid_ask_spread": float(metrics.get('bid_ask_spread', 0)),
        "order_book_bias": metrics.get('order_book_bias', 'neutral'),
        "bid_depth": float(metrics.get('bid_depth', 0)),
        "ask_depth": float(metrics.get('ask_depth', 0)),
        "calculated_at": timezone.now(),
    }
    fs.set(Collection.QUANT_METRICS, market_id, doc, merge=True)
    logger.info(f"Quant metrics saved to Firestore for {market_id}")


def fetch_price_history(market_id, bayse_market_id, title):
    """Fetch price history from Bayse — no SQLite storage needed."""
    try:
        history = bayse_client.get_price_history(
            event_id=market_id,
            outcome='YES',
            time_period='24H',
            market_id=bayse_market_id,
        )
        return history if history else []
    except BayseAPIError as e:
        logger.warning(f"Price history unavailable for {title}: {e}")
        return []


def fetch_ticker_data(market_id, bayse_market_id, title):
    """Fetch current ticker from Bayse."""
    try:
        if not bayse_market_id:
            return {}
        ticker = bayse_client.get_ticker(market_id=bayse_market_id, outcome='YES')
        # Update market price in Firestore
        if ticker and ticker.get('lastPrice'):
            fs.update(Collection.MARKETS, market_id, {
                "current_price": float(ticker['lastPrice']),
            })
        return ticker or {}
    except BayseAPIError as e:
        logger.warning(f"Ticker unavailable for {title}: {e}")
        return {}


def fetch_order_book(market_id):
    """Fetch order book from Bayse."""
    try:
        outcome_id = bayse_client.get_outcome_id(market_id, outcome_label='YES')
        if not outcome_id:
            return {}
        return bayse_client.get_order_book(outcome_id=outcome_id, depth=10) or {}
    except BayseAPIError as e:
        logger.warning(f"Order book unavailable for {market_id}: {e}")
        return {}


def calculate_momentum_metrics(price_history):
    """Calculate momentum from price history."""
    if not price_history:
        return {'momentum_score': 0, 'momentum_direction': 'neutral',
                'price_change_1h': 0, 'price_change_6h': 0, 'price_change_24h': 0}
    try:
        prices = [float(p.get('price', 0)) for p in price_history[-24:]]
        current = prices[-1] if prices else 0
        score = calculate_momentum(prices, normalize=True)
        direction = get_momentum_direction(score)
        return {
            'momentum_score': score, 'momentum_direction': direction,
            'price_change_1h': _pct_change(prices, -1, current),
            'price_change_6h': _pct_change(prices, -6, current),
            'price_change_24h': _pct_change(prices, -24, current),
        }
    except Exception as e:
        logger.error(f"Momentum calc error: {e}")
        return {'momentum_score': 0, 'momentum_direction': 'neutral',
                'price_change_1h': 0, 'price_change_6h': 0, 'price_change_24h': 0}


def _pct_change(prices, idx, current):
    try:
        if len(prices) < abs(idx) or prices[idx] == 0:
            return 0
        return round((current - prices[idx]) / prices[idx], 6)
    except:
        return 0


def calculate_volume_metrics(price_history, ticker_data):
    if not price_history:
        return {'volume_acceleration': 1.0, 'volume_trend': 'stable'}
    try:
        volumes = [float(p.get('volume', 0)) for p in price_history]
        recent = sum(volumes[-3:]) if len(volumes) >= 3 else sum(volumes)
        previous = sum(volumes[-6:-3]) if len(volumes) >= 6 else recent
        accel = calculate_volume_acceleration(recent, previous)
        trend = get_volume_trend(accel)
        return {'volume_acceleration': accel, 'volume_trend': trend}
    except Exception as e:
        logger.error(f"Volume calc error: {e}")
        return {'volume_acceleration': 1.0, 'volume_trend': 'stable'}


def calculate_order_book_metrics(order_book_data):
    if not order_book_data:
        return {'bid_ask_spread': 0, 'order_book_bias': 'neutral',
                'bid_depth': 0, 'ask_depth': 0}
    try:
        bids = order_book_data.get('bids', [])
        asks = order_book_data.get('asks', [])
        best_bid = float(bids[0]['price']) if bids else 0
        best_ask = float(asks[0]['price']) if asks else 0
        bid_depth = sum(float(b.get('quantity', 0)) for b in bids)
        ask_depth = sum(float(a.get('quantity', 0)) for a in asks)
        return {
            'bid_ask_spread': calculate_bid_ask_spread(best_bid, best_ask),
            'order_book_bias': get_order_book_bias(bid_depth, ask_depth),
            'bid_depth': Decimal(str(bid_depth)),
            'ask_depth': Decimal(str(ask_depth)),
        }
    except Exception as e:
        logger.error(f"Order book calc error: {e}")
        return {'bid_ask_spread': 0, 'order_book_bias': 'neutral',
                'bid_depth': 0, 'ask_depth': 0}
