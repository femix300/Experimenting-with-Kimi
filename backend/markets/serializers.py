"""
Serializers for Market data - Hybrid Friendly (SQLite & Firestore)
"""
from rest_framework import serializers
from .models import Market, QuantMetrics, PriceHistory

class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ['price', 'volume', 'timestamp']

class QuantMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuantMetrics
        fields = [
            'momentum_score', 'momentum_direction', 'price_change_1h',
            'price_change_6h', 'price_change_24h', 'volume_acceleration',
            'volume_trend', 'bid_ask_spread', 'order_book_bias',
            'bid_depth', 'ask_depth', 'calculated_at',
        ]

class MarketListSerializer(serializers.ModelSerializer):
    time_remaining_hours = serializers.SerializerMethodField()
    has_active_signal = serializers.SerializerMethodField()

    class Meta:
        model = Market
        fields = [
            'id', 'bayse_event_id', 'title', 'category', 'current_price',
            'implied_probability', 'volume_24h', 'liquidity', 'status',
            'signal_potential_score', 'time_remaining_hours', 
            'has_active_signal', 'closes_at',
        ]

    def get_time_remaining_hours(self, obj):
        if isinstance(obj, dict):
            return obj.get('time_remaining', 0)
        return getattr(obj, 'time_remaining', 0)

    def get_has_active_signal(self, obj):
        if isinstance(obj, dict):
            return obj.get('has_active_signal', False)
        # Use try-except to handle cases where the relationship isn't loaded
        try:
            return obj.signals.filter(is_active=True).exists()
        except:
            return False

class MarketDetailSerializer(serializers.ModelSerializer):
    latest_quant_metrics = serializers.SerializerMethodField()
    price_history = serializers.SerializerMethodField()
    time_remaining_hours = serializers.SerializerMethodField()

    class Meta:
        model = Market
        fields = [
            'id', 'bayse_event_id', 'bayse_market_id', 'title', 'description',
            'category', 'current_price', 'implied_probability', 'volume_24h',
            'total_volume', 'liquidity', 'status', 'signal_potential_score',
            'opens_at', 'closes_at', 'time_remaining_hours',
            'latest_quant_metrics', 'price_history', 'created_at', 'updated_at',
        ]

    def get_latest_quant_metrics(self, obj):
        if isinstance(obj, dict):
            # Return nested dict if it exists in Firestore doc
            return obj.get('latest_quant_metrics')
        
        try:
            latest = obj.quant_metrics.latest()
            return QuantMetricsSerializer(latest).data
        except:
            return None

    def get_price_history(self, obj):
        if isinstance(obj, dict):
            return obj.get('price_history', [])
            
        history = obj.price_history.all()[:100]
        return PriceHistorySerializer(history, many=True).data

    def get_time_remaining_hours(self, obj):
        if isinstance(obj, dict):
            return obj.get('time_remaining', 0)
        return getattr(obj, 'time_remaining', 0)