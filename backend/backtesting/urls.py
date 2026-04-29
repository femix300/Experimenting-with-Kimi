"""
URL routing for Backtesting API
"""
from django.urls import path
from .views import BacktestViewSet

urlpatterns = [
    path('strategies/', BacktestViewSet.as_view({'get': 'strategies'})),
    path('results/', BacktestViewSet.as_view({'get': 'results'})),
    path('run/', BacktestViewSet.as_view({'post': 'run'})),
]
