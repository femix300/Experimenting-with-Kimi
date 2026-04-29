from django.contrib import admin
from .models import BacktestStrategy, BacktestResult


@admin.register(BacktestStrategy)
class BacktestStrategyAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'min_edge_score', 'use_kelly', 'created_at']
    list_filter = ['use_kelly']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BacktestResult)
class BacktestResultAdmin(admin.ModelAdmin):
    list_display = ['strategy', 'start_date', 'end_date', 'total_trades', 'win_rate', 'total_return_pct', 'created_at']
    list_filter = ['start_date', 'end_date']
    readonly_fields = ['created_at']