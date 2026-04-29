"""
Serializers for Portfolio data
"""
from rest_framework import serializers
from .models import UserProfile, Trade, PortfolioSnapshot
from signals.serializers import SignalListSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    
    username = serializers.CharField(source='user.username', read_only=True)
    win_rate = serializers.SerializerMethodField()
    kelly_multiplier = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'username',
            'bankroll',
            'risk_tolerance',
            'total_trades',
            'winning_trades',
            'total_pnl',
            'win_rate',
            'kelly_multiplier',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['total_trades', 'winning_trades', 'total_pnl']
    
    def get_win_rate(self, obj):
        return obj.win_rate
    
    def get_kelly_multiplier(self, obj):
        return obj.kelly_multiplier


class TradeSerializer(serializers.ModelSerializer):
    """Serializer for trades"""
    
    signal_info = SignalListSerializer(source='signal', read_only=True)
    market_title = serializers.CharField(source='market.title', read_only=True)
    
    class Meta:
        model = Trade
        fields = [
            'id',
            'market_title',
            'signal_info',
            'direction',
            'stake_amount',
            'entry_price',
            'exit_price',
            'pnl',
            'roi',
            'recommended_stake',
            'kelly_compliant',
            'status',
            'opened_at',
            'closed_at',
        ]
        read_only_fields = ['pnl', 'roi', 'kelly_compliant']


class TradeCreateSerializer(serializers.Serializer):
    """Serializer for creating a new trade"""
    
    signal_id = serializers.IntegerField()
    stake_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    def validate_stake_amount(self, value):
        """Validate stake is positive"""
        if value <= 0:
            raise serializers.ValidationError("Stake amount must be positive")
        return value


class PortfolioSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for portfolio snapshots"""
    
    class Meta:
        model = PortfolioSnapshot
        fields = [
            'snapshot_date',
            'total_value',
            'total_pnl',
            'win_rate',
            'sharpe_ratio',
            'max_drawdown',
        ]