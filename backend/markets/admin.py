from django.contrib import admin
from .models import Market, QuantMetrics, PriceHistory

# Register your models here.
@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'current_price', 'implied_probability', 'volume_24h', 'created_at']
    list_filter = ['status', 'category']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(QuantMetrics)
class QuantMetricsAdmin(admin.ModelAdmin):
    list_display = ['market', 'momentum_score', 'momentum_direction', 'volume_acceleration', 'calculated_at']
    list_filter = ['momentum_direction', 'volume_trend']
    readonly_fields = ['calculated_at']

@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['market', 'price', 'volume', 'timestamp']
    list_filter = ['timestamp']
    readonly_fields = ['created_at']