"""
URL routing for Markets API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MarketViewSet

router = DefaultRouter()
router.register(r'', MarketViewSet, basename='market')

urlpatterns = [
    path('', include(router.urls)),
]