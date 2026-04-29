"""
Quantitative finance calculations
Kelly Criterion, Expected Value, Momentum, etc.
"""
import numpy as np
from decimal import Decimal
from scipy import stats
import logging

logger = logging.getLogger(__name__)


def calculate_momentum(prices, normalize=True):
    """
    Calculate price momentum using linear regression
    
    Args:
        prices: List or array of price values
        normalize: If True, return normalized score -100 to +100
        
    Returns:
        Momentum score (slope of price trend)
    """
    if len(prices) < 2:
        return 0
    
    try:
        # Convert to numpy array
        prices = np.array([float(p) for p in prices])
        
        # Time points (0, 1, 2, ..., n)
        x = np.arange(len(prices))
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, prices)
        
        if normalize:
            # Normalize slope to -100 to +100 scale
            # Scale based on average price to make it relative
            avg_price = np.mean(prices)
            if avg_price > 0:
                # Percentage change per time unit
                normalized_slope = (slope / avg_price) * 100
                # Clamp to -100 to +100
                momentum = max(-100, min(100, normalized_slope * 1000))  # Scale up for visibility
            else:
                momentum = 0
        else:
            momentum = slope
        
        return round(float(momentum), 2)
        
    except Exception as e:
        logger.error(f"Error calculating momentum: {str(e)}")
        return 0


def get_momentum_direction(momentum_score):
    """
    Convert momentum score to direction label
    
    Args:
        momentum_score: Numeric momentum (-100 to +100)
        
    Returns:
        'bullish', 'bearish', or 'neutral'
    """
    if momentum_score > 10:
        return 'bullish'
    elif momentum_score < -10:
        return 'bearish'
    else:
        return 'neutral'


def calculate_volume_acceleration(recent_volume, previous_volume):
    """
    Calculate volume acceleration ratio
    
    Args:
        recent_volume: Volume in recent period
        previous_volume: Volume in previous period
        
    Returns:
        Acceleration ratio (1.0 = no change, >1 = increasing, <1 = decreasing)
    """
    try:
        recent = float(recent_volume) if recent_volume else 0
        previous = float(previous_volume) if previous_volume else 0
        
        if previous == 0:
            return 1.0 if recent == 0 else 2.0  # If previous was 0 but now has volume, call it 2x
        
        acceleration = recent / previous
        return round(acceleration, 4)
        
    except Exception as e:
        logger.error(f"Error calculating volume acceleration: {str(e)}")
        return 1.0


def get_volume_trend(acceleration):
    """
    Convert volume acceleration to trend label
    
    Args:
        acceleration: Volume acceleration ratio
        
    Returns:
        'increasing', 'decreasing', or 'stable'
    """
    if acceleration > 1.2:
        return 'increasing'
    elif acceleration < 0.8:
        return 'decreasing'
    else:
        return 'stable'


def calculate_bid_ask_spread(best_bid, best_ask):
    """
    Calculate bid-ask spread
    
    Args:
        best_bid: Highest buy price
        best_ask: Lowest sell price
        
    Returns:
        Spread (difference between ask and bid)
    """
    try:
        bid = float(best_bid) if best_bid else 0
        ask = float(best_ask) if best_ask else 0
        
        spread = ask - bid
        return round(spread, 6)
        
    except Exception as e:
        logger.error(f"Error calculating spread: {str(e)}")
        return 0


def get_order_book_bias(bid_depth, ask_depth):
    """
    Determine order book bias based on bid/ask depth
    
    Args:
        bid_depth: Total volume on buy side
        ask_depth: Total volume on sell side
        
    Returns:
        'bullish', 'bearish', or 'neutral'
    """
    try:
        bid = float(bid_depth) if bid_depth else 0
        ask = float(ask_depth) if ask_depth else 0
        
        if bid == 0 and ask == 0:
            return 'neutral'
        
        total = bid + ask
        bid_ratio = bid / total if total > 0 else 0
        
        if bid_ratio > 0.6:  # 60% or more on buy side
            return 'bullish'
        elif bid_ratio < 0.4:  # 40% or less on buy side
            return 'bearish'
        else:
            return 'neutral'
            
    except Exception as e:
        logger.error(f"Error calculating order book bias: {str(e)}")
        return 'neutral'


def calculate_expected_value(win_probability, payout, loss_probability, stake):
    """
    Calculate Expected Value (EV)
    
    Args:
        win_probability: Probability of winning (0-1)
        payout: Amount won if successful
        loss_probability: Probability of losing (0-1)
        stake: Amount risked
        
    Returns:
        Expected value per unit staked
    """
    try:
        win_prob = float(win_probability)
        lose_prob = float(loss_probability)
        payout_amt = float(payout)
        stake_amt = float(stake)
        
        ev = (win_prob * payout_amt) - (lose_prob * stake_amt)
        
        # Return EV per unit staked
        if stake_amt > 0:
            return round(ev / stake_amt, 6)
        return 0
        
    except Exception as e:
        logger.error(f"Error calculating EV: {str(e)}")
        return 0


def calculate_kelly_fraction(edge, odds):
    """
    Calculate Kelly Criterion fraction
    
    Formula: Kelly % = Edge / Odds
    
    Args:
        edge: Your advantage (as decimal, e.g., 0.25 for 25%)
        odds: Decimal odds (e.g., 2.5 means you win 2.5x your stake)
        
    Returns:
        Kelly fraction (percentage of bankroll to bet)
    """
    try:
        edge_decimal = float(edge)
        odds_decimal = float(odds)
        
        if odds_decimal <= 0:
            return 0
        
        # Kelly formula
        kelly = edge_decimal / odds_decimal
        
        # Kelly should be between 0 and 1
        kelly = max(0, min(1, kelly))
        
        return round(kelly, 4)
        
    except Exception as e:
        logger.error(f"Error calculating Kelly: {str(e)}")
        return 0


def calculate_kelly_stake(bankroll, edge, odds, risk_tolerance='balanced'):
    """
    Calculate recommended stake using Kelly Criterion
    
    Args:
        bankroll: Total available capital
        edge: Your advantage (as decimal)
        odds: Decimal odds
        risk_tolerance: 'conservative', 'balanced', or 'aggressive'
        
    Returns:
        Dictionary with stake amounts for each risk level
    """
    try:
        kelly_fraction = calculate_kelly_fraction(edge, odds)
        bankroll_amt = float(bankroll)
        
        # Risk multipliers
        multipliers = {
            'conservative': 0.25,  # Quarter Kelly
            'balanced': 0.5,       # Half Kelly
            'aggressive': 1.0,     # Full Kelly
        }
        
        stakes = {}
        for tolerance, multiplier in multipliers.items():
            stake = bankroll_amt * kelly_fraction * multiplier
            stakes[tolerance] = round(stake, 2)
        
        return stakes
        
    except Exception as e:
        logger.error(f"Error calculating Kelly stake: {str(e)}")
        return {
            'conservative': 0,
            'balanced': 0,
            'aggressive': 0
        }


def calculate_decimal_odds(market_price):
    """
    Convert market price to decimal odds
    
    For prediction markets:
    If price = 0.40 (40% implied probability)
    Decimal odds = 1 / 0.40 = 2.5
    
    Args:
        market_price: Current market price (0-1 range)
        
    Returns:
        Decimal odds
    """
    try:
        price = float(market_price)
        
        if price <= 0 or price >= 1:
            return 1.0
        
        odds = 1 / price
        return round(odds, 4)
        
    except Exception as e:
        logger.error(f"Error calculating decimal odds: {str(e)}")
        return 1.0


def calculate_implied_probability(price):
    """
    Convert price to implied probability percentage
    
    Args:
        price: Market price (0-1 range or 0-100 range)
        
    Returns:
        Implied probability (0-100)
    """
    try:
        p = float(price)
        
        # If already in percentage form (0-100)
        if p > 1:
            return round(p, 2)
        
        # Convert from 0-1 to 0-100
        return round(p * 100, 2)
        
    except Exception as e:
        logger.error(f"Error calculating implied probability: {str(e)}")
        return 0


def calculate_edge(ai_probability, market_probability):
    """
    Calculate edge (difference between true and implied probability)
    
    Args:
        ai_probability: AI's estimated probability (0-100)
        market_probability: Market's implied probability (0-100)
        
    Returns:
        Edge in percentage points
    """
    try:
        ai_prob = float(ai_probability)
        market_prob = float(market_probability)
        
        edge = ai_prob - market_prob
        return round(edge, 2)
        
    except Exception as e:
        logger.error(f"Error calculating edge: {str(e)}")
        return 0


def calculate_sharpe_ratio(returns, risk_free_rate=0):
    """
    Calculate Sharpe Ratio
    
    Args:
        returns: List of periodic returns
        risk_free_rate: Risk-free rate of return
        
    Returns:
        Sharpe ratio
    """
    try:
        returns_array = np.array([float(r) for r in returns])
        
        if len(returns_array) < 2:
            return 0
        
        excess_returns = returns_array - risk_free_rate
        avg_excess_return = np.mean(excess_returns)
        std_dev = np.std(excess_returns)
        
        if std_dev == 0:
            return 0
        
        sharpe = avg_excess_return / std_dev
        return round(float(sharpe), 4)
        
    except Exception as e:
        logger.error(f"Error calculating Sharpe ratio: {str(e)}")
        return 0


def calculate_max_drawdown(equity_curve):
    """
    Calculate maximum drawdown
    
    Args:
        equity_curve: List of portfolio values over time
        
    Returns:
        Maximum drawdown (absolute and percentage)
    """
    try:
        curve = np.array([float(v) for v in equity_curve])
        
        if len(curve) < 2:
            return {'absolute': 0, 'percentage': 0}
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(curve)
        
        # Calculate drawdown at each point
        drawdown = running_max - curve
        
        # Find maximum drawdown
        max_dd = np.max(drawdown)
        
        # Find the peak where max drawdown occurred
        max_dd_idx = np.argmax(drawdown)
        peak_value = running_max[max_dd_idx]
        
        # Calculate percentage drawdown
        max_dd_pct = (max_dd / peak_value * 100) if peak_value > 0 else 0
        
        return {
            'absolute': round(float(max_dd), 2),
            'percentage': round(float(max_dd_pct), 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating max drawdown: {str(e)}")
        return {'absolute': 0, 'percentage': 0}


def calculate_win_rate(trades):
    """
    Calculate win rate from list of trades
    
    Args:
        trades: List of trade objects with 'pnl' field
        
    Returns:
        Win rate percentage
    """
    try:
        if not trades:
            return 0
        
        winning_trades = sum(1 for trade in trades if float(trade.get('pnl', 0)) > 0)
        total_trades = len(trades)
        
        win_rate = (winning_trades / total_trades) * 100
        return round(win_rate, 2)
        
    except Exception as e:
        logger.error(f"Error calculating win rate: {str(e)}")
        return 0
