"""
Serializers for Backtesting
"""
from rest_framework import serializers
from .models import BacktestStrategy, BacktestResult


class BacktestStrategySerializer(serializers.ModelSerializer):
    """Serializer for backtest strategies"""

    class Meta:
        model = BacktestStrategy
        fields = [
            'id',
            'name',
            'description',
            'min_edge_score',
            'min_momentum',
            'max_spread',
            'min_confidence',
            'categories',
            'max_stake_per_trade',
            'use_kelly',
            'created_at',
        ]


class BacktestResultSerializer(serializers.ModelSerializer):
    """Serializer for backtest results"""

    strategy_name = serializers.CharField(
        source='strategy.name', read_only=True)

    class Meta:
        model = BacktestResult
        fields = [
            'id',
            'strategy_name',
            'start_date',
            'end_date',
            'initial_bankroll',
            'total_trades',
            'winning_trades',
            'losing_trades',
            'win_rate',
            'total_return',
            'total_return_pct',
            'final_bankroll',
            'max_drawdown',
            'max_drawdown_pct',
            'sharpe_ratio',
            'ai_review',
            'created_at',
        ]
