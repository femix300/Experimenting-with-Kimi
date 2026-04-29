"""
Backtesting models - strategy testing
"""
from django.db import models
from django.contrib.auth.models import User


class BacktestStrategy(models.Model):
    """
    A backtesting strategy configuration
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='strategies')
    
    # Strategy details
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Strategy rules
    min_edge_score = models.DecimalField(max_digits=5, decimal_places=2)
    min_momentum = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_spread = models.DecimalField(max_digits=6, decimal_places=6, null=True, blank=True)
    min_confidence = models.IntegerField(null=True, blank=True)
    categories = models.JSONField(default=list)  # ['crypto', 'sports']
    
    # Risk management
    max_stake_per_trade = models.DecimalField(max_digits=5, decimal_places=2)  # % of bankroll
    use_kelly = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Backtest strategies'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} by {self.user.username}"


class BacktestResult(models.Model):
    """
    Results from running a backtest
    """
    strategy = models.ForeignKey(BacktestStrategy, on_delete=models.CASCADE, related_name='results')
    
    # Backtest parameters
    start_date = models.DateField()
    end_date = models.DateField()
    initial_bankroll = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Performance metrics
    total_trades = models.IntegerField()
    winning_trades = models.IntegerField()
    losing_trades = models.IntegerField()
    win_rate = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Returns
    total_return = models.DecimalField(max_digits=15, decimal_places=2)
    total_return_pct = models.DecimalField(max_digits=10, decimal_places=2)
    final_bankroll = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Risk metrics
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=2)
    max_drawdown_pct = models.DecimalField(max_digits=5, decimal_places=2)
    sharpe_ratio = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    
    # Trade log (stored as JSON)
    trade_log = models.JSONField(default=list)
    
    # AI review
    ai_review = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Backtest: {self.strategy.name} ({self.start_date} to {self.end_date})"