"""
URL routing for Markets API
"""
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import MarketViewSet
from .sse_views import sse_analyze_view

router = DefaultRouter()
router.register(r'', MarketViewSet, basename='market')

urlpatterns = [
    # SSE streaming endpoint (must come before router to avoid pk conflicts)
    re_path(r'^(?P<pk>[^/]+)/analyze_stream/$', sse_analyze_view, name='market-analyze-stream'),
    path('', include(router.urls)),
]
