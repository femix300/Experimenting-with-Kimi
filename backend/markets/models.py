"""
Market models - stores Bayse market data
"""
from django.db import models
from django.utils import timezone


class Market(models.Model):
    """
    Represents a prediction market from Bayse
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    ]

    CATEGORY_CHOICES = [
        ('crypto', 'Cryptocurrency'),
        ('sports', 'Sports'),
        ('politics', 'Politics'),
        ('entertainment', 'Entertainment'),
        ('other', 'Other'),
    ]

    # Bayse identifiers
    bayse_event_id = models.CharField(
        max_length=100, unique=True, db_index=True)
    bayse_market_id = models.CharField(max_length=100, blank=True, null=True)

    # Market details
    title = models.TextField()
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, default='other')

    # Price and trading data
    current_price = models.DecimalField(
        max_digits=10, decimal_places=6, default=0)
    implied_probability = models.DecimalField(
        max_digits=5, decimal_places=2, default=0)  # 0-100

    # Volume and liquidity
    volume_24h = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)
    total_volume = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)
    liquidity = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Market status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active')

    # Timing
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Resolution (for backtesting)
    resolution = models.CharField(
        max_length=10, blank=True)  # 'YES', 'NO', or empty

    # Metadata
    signal_potential_score = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    last_scanned_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-signal_potential_score', '-volume_24h']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['signal_potential_score']),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"

    @property
    def time_remaining(self):
        """Calculate time remaining until market closes"""
        if self.closes_at:
            delta = self.closes_at - timezone.now()
            return delta.total_seconds() / 3600  # hours
        return None

    @property
    def is_active(self):
        """Check if market is currently active"""
        return self.status == 'active' and self.closes_at and self.closes_at > timezone.now()


class QuantMetrics(models.Model):
    """
    Stores quantitative analysis metrics for a market
    Calculated by Agent 02
    """
    market = models.ForeignKey(
        Market, on_delete=models.CASCADE, related_name='quant_metrics')

    # Momentum analysis
    momentum_score = models.DecimalField(
        max_digits=6, decimal_places=2)  # -100 to +100
    momentum_direction = models.CharField(
        max_length=20)  # 'bullish', 'bearish', 'neutral'
    price_change_1h = models.DecimalField(
        max_digits=10, decimal_places=6, default=0)
    price_change_6h = models.DecimalField(
        max_digits=10, decimal_places=6, default=0)
    price_change_24h = models.DecimalField(
        max_digits=10, decimal_places=6, default=0)

    # Volume analysis
    volume_acceleration = models.DecimalField(
        max_digits=6, decimal_places=4)  # ratio
    # 'increasing', 'decreasing', 'stable'
    volume_trend = models.CharField(max_length=20)

    # Order book analysis
    bid_ask_spread = models.DecimalField(max_digits=6, decimal_places=6)
    # 'bullish', 'bearish', 'neutral'
    order_book_bias = models.CharField(max_length=20)
    bid_depth = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ask_depth = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Timestamps
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-calculated_at']
        get_latest_by = 'calculated_at'
        verbose_name_plural = 'Quant metrics'

    def __str__(self):
        return f"{self.market.title} - Metrics at {self.calculated_at}"


class PriceHistory(models.Model):
    """
    Historical price points for backtesting and charting
    """
    market = models.ForeignKey(
        Market, on_delete=models.CASCADE, related_name='price_history')

    price = models.DecimalField(max_digits=10, decimal_places=6)
    volume = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    timestamp = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['market', 'timestamp']),
        ]
        verbose_name_plural = 'Price history'

    def __str__(self):
        return f"{self.market.title} - ₦{self.price} at {self.timestamp}"
