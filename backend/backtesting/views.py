"""
API views for Backtesting - Firestore based
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .engine import run_backtest_simulation
from utils.firebase_client import fs, Collection
import logging

logger = logging.getLogger(__name__)


class BacktestViewSet(viewsets.ViewSet):
    """
    API endpoints for backtesting
    """
    
    def _get_user_id(self, request):
        if request.user.is_authenticated:
            return str(request.user.username)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from firebase_admin import auth as firebase_auth
                token = auth_header[7:]
                decoded = firebase_auth.verify_id_token(token, check_revoked=False)
                uid = decoded.get("uid")
                if uid:
                    return uid
            except Exception:
                pass
        return None

    def strategies(self, request):
        """
        Get predefined backtest strategies
        
        GET /api/backtest/strategies/
        """
        strategies = [
            {
                "id": "momentum_edge",
                "name": "Momentum + Edge",
                "description": "Buy when momentum > 10% and edge > 15%",
                "params": {"min_edge": 15, "min_momentum": 10}
            },
            {
                "id": "high_confidence",
                "name": "High Confidence",
                "description": "Only trades with confidence > 70%",
                "params": {"min_edge": 20, "min_confidence": 70}
            },
            {
                "id": "aggressive",
                "name": "Aggressive",
                "description": "Lower edge threshold, more trades",
                "params": {"min_edge": 5, "min_momentum": 5}
            },
            {
                "id": "conservative",
                "name": "Conservative",
                "description": "High edge threshold, fewer trades",
                "params": {"min_edge": 25}
            }
        ]
        
        return Response({
            'success': True,
            'count': len(strategies),
            'strategies': strategies,
        })
    
    @action(detail=False, methods=['get'])
    def results(self, request):
        """
        Get previous backtest results from Firestore
        
        GET /api/backtest/results/
        """
        user_id = self._get_user_id(request)
        results = fs.query(
            collection=Collection.BACKTEST_RESULTS,
            filters=[("user_id", "==", user_id)],
            order_by=("created_at", True),
            limit=20,
        )
        
        return Response({
            'success': True,
            'count': len(results),
            'results': results,
        })
    
    @action(detail=False, methods=['post'])
    def run(self, request):
        """
        Run a backtest
        
        POST /api/backtest/run/
        Body: {
            "strategy_config": {
                "min_edge": 20,
                "min_momentum": 10,
                "categories": ["crypto"]
            },
            "initial_bankroll": 10000
        }
        """
        try:
            user_id = self._get_user_id(request)
            strategy_config = request.data.get('strategy_config', {})
            initial_bankroll = float(request.data.get('initial_bankroll', 10000))
            
            # Run simulation
            result = run_backtest_simulation(strategy_config, initial_bankroll)
            
            # Save result to Firestore
            from django.utils import timezone
            doc_id = f"backtest_{user_id}_{timezone.now().timestamp()}"
            
            backtest_doc = {
                "user_id": user_id,
                "strategy_config": strategy_config,
                "initial_bankroll": initial_bankroll,
                "results": result,
                "created_at": timezone.now(),
            }
            
            fs.set(Collection.BACKTEST_RESULTS, doc_id, backtest_doc)
            
            return Response({
                'success': True,
                'result': result,
                'message': f'Backtest completed: {result["total_trades"]} trades analyzed'
            })
            
        except Exception as e:
            logger.error(f"Backtest error: {str(e)}")
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
