from django.db import models
from markets.models import Market

# Create your models here.

"""
Signal models - stores AI-generated trading signals
"""

class Signal(models.Model):
    """
    AI-generated trading signal
    Created by Agent 04
    """
    DIRECTION_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
        ('WAIT', 'Wait'),
    ]
    
    CONFIDENCE_LEVEL_CHOICES = [
        ('low', 'Low (0-40%)'),
        ('medium', 'Medium (40-70%)'),
        ('high', 'High (70-100%)'),
    ]

    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='signals')
    
    # Signal direction and strength
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    edge_score = models.DecimalField(max_digits=5, decimal_places=2)  # percentage points
    expected_value = models.DecimalField(max_digits=10, decimal_places=6)  # ₦ per naira staked
    
    # Probability estimates
    market_probability = models.DecimalField(max_digits=5, decimal_places=2)  # 0-100
    ai_probability = models.DecimalField(max_digits=5, decimal_places=2)  # 0-100
    confidence = models.IntegerField()  # 0-100
    confidence_level = models.CharField(max_length=20, choices=CONFIDENCE_LEVEL_CHOICES)
    
    # Kelly Criterion recommendations
    kelly_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # % of bankroll
    recommended_stake_conservative = models.DecimalField(max_digits=10, decimal_places=2)
    recommended_stake_balanced = models.DecimalField(max_digits=10, decimal_places=2)
    recommended_stake_aggressive = models.DecimalField(max_digits=10, decimal_places=2)
    
    # AI reasoning
    reasoning = models.TextField()
    news_context = models.TextField(blank=True)  # News snippets from Gemini
    
    # Signal metadata
    is_active = models.BooleanField(default=True)
    signal_strength = models.CharField(max_length=20)  # 'strong', 'moderate', 'weak'
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-edge_score', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'edge_score']),
            models.Index(fields=['direction', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.direction} {self.market.title} - Edge: {self.edge_score}%"
    
    def save(self, *args, **kwargs):
        # Auto-set confidence level based on confidence score
        if self.confidence >= 70:
            self.confidence_level = 'high'
        elif self.confidence >= 40:
            self.confidence_level = 'medium'
        else:
            self.confidence_level = 'low'
        
        # Auto-set signal strength based on edge score
        if self.edge_score >= 25:
            self.signal_strength = 'strong'
        elif self.edge_score >= 15:
            self.signal_strength = 'moderate'
        else:
            self.signal_strength = 'weak'
        
        super().save(*args, **kwargs)

class AIAnalysis(models.Model):
    """
    Stores raw AI probability analysis from Agent 03
    """
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='ai_analyses')
    signal = models.ForeignKey(Signal, on_delete=models.CASCADE, null=True, blank=True, related_name='ai_analysis')
    
    # AI estimates
    estimated_probability = models.DecimalField(max_digits=5, decimal_places=2)
    confidence_score = models.IntegerField()
    
    # AI reasoning
    reasoning_summary = models.TextField()
    sources_consulted = models.TextField(blank=True)  # List of sources Gemini found
    
    # Gemini metadata
    model_used = models.CharField(max_length=50, default='gemini-2.5-flash')
    search_grounding_used = models.BooleanField(default=True)
    
    # Timestamps
    analyzed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-analyzed_at']
        verbose_name_plural = 'AI analyses'
    
    def __str__(self):
        return f"AI Analysis: {self.market.title} - {self.estimated_probability}%"