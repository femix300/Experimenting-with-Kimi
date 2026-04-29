from django.contrib import admin
from .models import Trade, PortfolioSnapshot


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'direction', 'stake_amount', 'status', 'opened_at']
    list_filter = ['status', 'direction']
    search_fields = ['user', 'market__title']
    readonly_fields = ['opened_at', 'closed_at']


@admin.register(PortfolioSnapshot)
class PortfolioSnapshotAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'bankroll', 'total_pnl', 'snapshot_date']
    list_filter = ['snapshot_date']
    search_fields = ['user']
