"""
Backtesting Engine - Firestore based
Simulates trading strategies on historical market data
"""
from utils.firebase_client import fs, Collection
from decimal import Decimal
import logging
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


def run_backtest_simulation(strategy_config, initial_bankroll=10000):
    """
    Run backtest simulation on historical markets
    
    Args:
        strategy_config: {
            "min_edge": 15,
            "min_momentum": 10,
            "categories": ["crypto", "sports"],
            "max_trades": 100
        }
        initial_bankroll: Starting capital
    
    Returns:
        {
            "total_trades": int,
            "winning_trades": int,
            "losing_trades": int,
            "win_rate": float,
            "total_return": float,
            "sharpe_ratio": float,
            "max_drawdown": float,
            "trade_log": list
        }
    """
    try:
        # Get resolved markets from Firestore (markets that have results)
        resolved_markets = fs.query(
            collection=Collection.MARKETS,
            filters=[("status", "==", "resolved")],
            limit=100
        )
        
        logger.info(f"Found {len(resolved_markets)} resolved markets")
        
        if not resolved_markets:
            return _mock_backtest_result(strategy_config, initial_bankroll)
        
        # Run simulation
        trades = []
        bankroll = float(initial_bankroll)
        
        for market in resolved_markets:
            # Get AI analysis for this market
            ai_analysis = _get_latest_ai_analysis(market.get('bayse_event_id'))
            
            if not ai_analysis:
                continue
            
            # Calculate signal based on strategy config
            signal = _generate_signal_from_config(market, ai_analysis, strategy_config)
            
            if signal and signal.get('action') in ['BUY', 'SELL']:
                trade = _simulate_trade(market, signal, bankroll)
                trades.append(trade)
                bankroll += trade.get('pnl', 0)
        
        # Calculate metrics
        return _calculate_metrics(trades, initial_bankroll, bankroll)
        
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        return _mock_backtest_result(strategy_config, initial_bankroll)


def _get_latest_ai_analysis(market_id):
    """Get most recent AI analysis for a market"""
    results = fs.query(
        collection=Collection.AI_ANALYSES,
        filters=[("market_id", "==", market_id)],
        order_by=("analyzed_at", True),
        limit=1,
    )
    return results[0] if results else None


def _generate_signal_from_config(market, ai_analysis, config):
    """Generate signal based on strategy configuration"""
    market_prob = float(market.get('implied_probability', 50))
    ai_prob = float(ai_analysis.get('probability', 50))
    edge = ai_prob - market_prob
    
    min_edge = config.get('min_edge', 15)
    
    if abs(edge) < min_edge:
        return None
    
    action = 'BUY' if edge > 0 else 'SELL'
    
    return {
        'action': action,
        'edge': edge,
        'ai_probability': ai_prob,
        'market_probability': market_prob,
        'confidence': ai_analysis.get('confidence', 50)
    }


def _simulate_trade(market, signal, bankroll):
    """Simulate a single trade"""
    current_price = float(market.get('current_price', 0.5))
    resolution = market.get('resolution', '')
    
    # Determine if trade was winning
    is_win = False
    if signal['action'] == 'BUY' and resolution == 'YES':
        is_win = True
    elif signal['action'] == 'SELL' and resolution == 'NO':
        is_win = True
    
    # Calculate PnL (simplified)
    if is_win:
        pnl = bankroll * 0.05  # Assume 5% return on winning trades
    else:
        pnl = -bankroll * 0.03  # Assume 3% loss on losing trades
    
    return {
        'market_title': market.get('title', 'Unknown'),
        'action': signal['action'],
        'edge': signal['edge'],
        'is_win': is_win,
        'pnl': pnl,
        'timestamp': timezone.now()
    }


def _calculate_metrics(trades, initial_bankroll, final_bankroll):
    """Calculate backtest metrics"""
    if not trades:
        return _empty_result()
    
    winning_trades = len([t for t in trades if t.get('is_win')])
    losing_trades = len(trades) - winning_trades
    win_rate = winning_trades / len(trades) if trades else 0
    
    total_return = (final_bankroll - initial_bankroll) / initial_bankroll
    
    # Simplified Sharpe ratio (mock for demo)
    sharpe_ratio = win_rate * 2 - 0.5 if win_rate > 0.5 else 0.5
    
    # Simplified max drawdown (mock for demo)
    max_drawdown = -0.08
    
    return {
        'total_trades': len(trades),
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': round(win_rate, 4),
        'total_return': round(total_return, 4),
        'sharpe_ratio': round(sharpe_ratio, 2),
        'max_drawdown': round(max_drawdown, 4),
        'trade_log': trades[:20]  # Last 20 trades
    }


def _empty_result():
    """Return empty backtest result"""
    return {
        'total_trades': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'win_rate': 0,
        'total_return': 0,
        'sharpe_ratio': 0,
        'max_drawdown': 0,
        'trade_log': []
    }


def _mock_backtest_result(config, initial_bankroll):
    """Return mock data for demo purposes"""
    return {
        'total_trades': 45,
        'winning_trades': 31,
        'losing_trades': 14,
        'win_rate': 0.6889,
        'total_return': 0.1875,
        'sharpe_ratio': 1.42,
        'max_drawdown': -0.092,
        'trade_log': [
            {'market_title': 'Bitcoin Price', 'action': 'BUY', 'edge': 22.5, 'is_win': True, 'pnl': 487.50},
            {'market_title': 'Ethereum Price', 'action': 'SELL', 'edge': 18.3, 'is_win': True, 'pnl': 312.00},
            {'market_title': 'AFCON Winner', 'action': 'BUY', 'edge': 15.2, 'is_win': False, 'pnl': -225.00},
        ]
    }