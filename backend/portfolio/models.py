"""
Portfolio Models - Firestore first, SQLite for compatibility
"""
from django.db import models
from markets.models import Market
from signals.models import Signal


class Trade(models.Model):
    """
    User trade record - stored in SQLite as backup, Firestore as primary
    """
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]
    
    DIRECTION_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    user = models.CharField(max_length=100, db_index=True)  # Store user_id
    signal = models.ForeignKey(Signal, on_delete=models.SET_NULL, null=True, blank=True)
    market = models.ForeignKey(Market, on_delete=models.SET_NULL, null=True, blank=True)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    stake_amount = models.DecimalField(max_digits=15, decimal_places=2)
    entry_price = models.DecimalField(max_digits=10, decimal_places=6)
    exit_price = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    pnl = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    roi = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    recommended_stake = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    kelly_compliant = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        market_title = self.market.title[:30] if self.market else "Unknown"
        return f"{self.direction} {market_title} - {self.status}"


class PortfolioSnapshot(models.Model):
    """
    Historical portfolio snapshot for performance tracking
    """
    user = models.CharField(max_length=100, db_index=True)
    bankroll = models.DecimalField(max_digits=15, decimal_places=2)
    total_pnl = models.DecimalField(max_digits=15, decimal_places=2)
    total_trades = models.IntegerField()
    winning_trades = models.IntegerField()
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sharpe_ratio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_drawdown = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    snapshot_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-snapshot_date']
    
    def __str__(self):
        return f"{self.user} - {self.snapshot_date.date()}"
