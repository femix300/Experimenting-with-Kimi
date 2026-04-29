from django.contrib import admin
from .models import Signal, AIAnalysis


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ['market', 'direction', 'edge_score', 'expected_value', 'confidence_level', 'signal_strength', 'created_at']
    list_filter = ['direction', 'confidence_level', 'signal_strength', 'is_active']
    search_fields = ['market__title', 'reasoning']
    readonly_fields = ['created_at', 'confidence_level', 'signal_strength']


@admin.register(AIAnalysis)
class AIAnalysisAdmin(admin.ModelAdmin):
    list_display = ['market', 'estimated_probability', 'confidence_score', 'model_used', 'analyzed_at']
    list_filter = ['model_used', 'search_grounding_used']
    readonly_fields = ['analyzed_at']