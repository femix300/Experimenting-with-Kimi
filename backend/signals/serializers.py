"""
Serializers for Signal data
"""
from rest_framework import serializers
from .models import Signal, AIAnalysis
from markets.serializers import MarketListSerializer


class AIAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for AI analysis"""
    
    class Meta:
        model = AIAnalysis
        fields = [
            'estimated_probability',
            'confidence_score',
            'reasoning_summary',
            'sources_consulted',
            'model_used',
            'analyzed_at',
        ]


class SignalSerializer(serializers.ModelSerializer):
    """Serializer for trading signals"""
    
    market = MarketListSerializer(read_only=True)
    ai_analysis = serializers.SerializerMethodField()
    
    class Meta:
        model = Signal
        fields = [
            'id',
            'market',
            'direction',
            'edge_score',
            'expected_value',
            'market_probability',
            'ai_probability',
            'confidence',
            'confidence_level',
            'kelly_percentage',
            'recommended_stake_conservative',
            'recommended_stake_balanced',
            'recommended_stake_aggressive',
            'reasoning',
            'news_context',
            'signal_strength',
            'is_active',
            'created_at',
            'expires_at',
            'ai_analysis',
        ]
    
    def get_ai_analysis(self, obj):
        """Get associated AI analysis"""
        try:
            analysis = obj.ai_analysis.first()
            if analysis:
                return AIAnalysisSerializer(analysis).data
        except:
            pass
        return None


class SignalListSerializer(serializers.ModelSerializer):
    """Lighter serializer for signal list"""
    
    market_title = serializers.CharField(source='market.title', read_only=True)
    market_category = serializers.CharField(source='market.category', read_only=True)
    market_id = serializers.IntegerField(source='market.id', read_only=True)
    
    class Meta:
        model = Signal
        fields = [
            'id',
            'market_id',
            'market_title',
            'market_category',
            'direction',
            'edge_score',
            'expected_value',
            'confidence_level',
            'signal_strength',
            'recommended_stake_balanced',
            'created_at',
        ]