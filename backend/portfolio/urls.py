"""
URL routing for Portfolio API
"""
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import PortfolioViewSet

urlpatterns = [
    path('profile/', PortfolioViewSet.as_view({'get': 'profile'})),
    path('update_profile/', csrf_exempt(PortfolioViewSet.as_view({'post': 'update_profile'}))),
    path('trades/', PortfolioViewSet.as_view({'get': 'trades'})),
    path('simulate_trade/', PortfolioViewSet.as_view({'post': 'simulate_trade'})),
    path('close_trade/', PortfolioViewSet.as_view({'post': 'close_trade'})),
    path('analytics/', PortfolioViewSet.as_view({'get': 'analytics'})),
]
