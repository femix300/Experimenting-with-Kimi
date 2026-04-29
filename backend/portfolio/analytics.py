"""
Portfolio analytics calculations
"""
from .models import Trade
from utils.calculations import calculate_sharpe_ratio, calculate_max_drawdown
from decimal import Decimal


def calculate_portfolio_metrics(user):
    """
    Calculate comprehensive portfolio metrics
    
    Args:
        user: User object
        
    Returns:
        Dictionary with portfolio metrics
    """
    profile = user.profile
    trades = Trade.objects.filter(user=user, status__in=['won', 'lost'])
    
    if not trades.exists():
        return {
            'total_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'avg_pnl_per_trade': 0,
            'kelly_compliance_rate': 0,
            'sharpe_ratio': 0,
            'max_drawdown': {'absolute': 0, 'percentage': 0},
            'qpi': 0,
        }
    
    # Basic metrics
    total_trades = trades.count()
    winning_trades = trades.filter(status='won').count()
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    
    total_pnl = sum(float(t.pnl) for t in trades if t.pnl)
    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
    
    # Kelly compliance
    kelly_compliant = trades.filter(kelly_compliant=True).count()
    kelly_compliance_rate = (kelly_compliant / total_trades) * 100 if total_trades > 0 else 0
    
    # Returns for Sharpe ratio
    returns = [float(t.roi) / 100 for t in trades if t.roi is not None]
    sharpe = calculate_sharpe_ratio(returns) if returns else 0
    
    # Equity curve for max drawdown
    equity_curve = []
    running_total = float(profile.bankroll)
    for trade in trades.order_by('closed_at'):
        if trade.pnl:
            running_total += float(trade.pnl)
            equity_curve.append(running_total)
    
    max_dd = calculate_max_drawdown(equity_curve) if equity_curve else {'absolute': 0, 'percentage': 0}
    
    # Quant Performance Index (QPI)
    # Weighted score: 30% win rate + 40% Kelly compliance + 30% Sharpe
    normalized_sharpe = min(100, max(0, (sharpe + 2) * 25))  # Normalize Sharpe to 0-100
    qpi = (win_rate * 0.3) + (kelly_compliance_rate * 0.4) + (normalized_sharpe * 0.3)
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'win_rate': round(win_rate, 2),
        'total_pnl': round(total_pnl, 2),
        'avg_pnl_per_trade': round(avg_pnl, 2),
        'kelly_compliance_rate': round(kelly_compliance_rate, 2),
        'sharpe_ratio': round(sharpe, 4),
        'max_drawdown': max_dd,
        'qpi': round(qpi, 2),
    }
