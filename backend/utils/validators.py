"""
Validation utilities
"""
from decimal import Decimal

def validate_probability(value):
    """
    Validate probability is between 0 and 100
    
    Args:
        value: Probability value to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        prob = float(value)
        return 0 <= prob <= 100
    except (ValueError, TypeError):
        return False

def validate_price(value):
    """
    Validate price is between 0 and 1
    
    Args:
        value: Price value to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        price = float(value)
        return 0 <= price <= 1
    except (ValueError, TypeError):
        return False

def validate_bankroll(value, min_amount=100):
    """
    Validate bankroll amount
    
    Args:
        value: Bankroll amount
        min_amount: Minimum allowed bankroll
        
    Returns:
        True if valid, False otherwise
    """
    try:
        bankroll = float(value)
        return bankroll >= min_amount
    except (ValueError, TypeError):
        return False

def validate_stake(stake, bankroll):
    """
    Validate stake doesn't exceed bankroll
    
    Args:
        stake: Stake amount
        bankroll: Available bankroll
        
    Returns:
        True if valid, False otherwise
    """
    try:
        stake_amt = float(stake)
        bankroll_amt = float(bankroll)
        return 0 < stake_amt <= bankroll_amt
    except (ValueError, TypeError):
        return False

def validate_risk_tolerance(value):
    """
    Validate risk tolerance setting
    
    Args:
        value: Risk tolerance value
        
    Returns:
        True if valid, False otherwise
    """
    valid_values = ['conservative', 'balanced', 'aggressive']
    return value in valid_values