"""
API views for Markets — Firestore-only (Cloud Run compatible)
"""
from utils.firebase_client import fs, Collection
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from services.bayse_client import bayse_client
from agents.market_scanner import scan_markets, get_top_markets
from agents.signal_generator import generate_signal
from .tasks import async_scan_markets, async_analyze_market
from celery.result import AsyncResult
import logging
import uuid

logger = logging.getLogger(__name__)


class MarketPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class MarketViewSet(viewsets.GenericViewSet):
    """
    Firestore-backed market endpoints. No SQLite dependency.
    
    list:      GET  /api/markets/
    retrieve:  GET  /api/markets/{firestore_doc_id}/
    scan:      POST /api/markets/scan/
    analyze:   POST /api/markets/{firestore_doc_id}/analyze/
    top:       GET  /api/markets/top/
    price_history: GET /api/markets/price_history/
    order_book:    GET /api/markets/order_book/
    """
    pagination_class = MarketPagination

    # ── list ──────────────────────────────────────────────────────────
    def list(self, request):
        """GET /api/markets/?status=open&category=sports"""
        status_filter = request.query_params.get('status', 'open')
        category = request.query_params.get('category')
        limit = int(request.query_params.get('page_size', 100))

        statuses = [s.strip() for s in status_filter.split(',') if s.strip()]
        filters = []
        if statuses:
            filters.append(("status", "in", statuses))
        if category:
            filters.append(("category", "==", category))

        markets = fs.query(
            collection=Collection.MARKETS,
            filters=filters if filters else None,
            order_by=("signal_potential_score", True),
            limit=limit,
        )

        # Enrich with time_remaining for frontend
        for m in markets:
            m["id"] = m.get("bayse_event_id", m.get("id", ""))
            m["time_remaining_hours"] = m.get("time_remaining", 0)

        # Manual pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        page_data = markets[start:end]

        return Response({
            "count": len(markets),
            "next": f"/api/markets/?page={page+1}&page_size={page_size}" if end < len(markets) else None,
            "previous": f"/api/markets/?page={page-1}&page_size={page_size}" if page > 1 else None,
            "results": page_data,
        })

    # ── retrieve ──────────────────────────────────────────────────────
    def retrieve(self, request, pk=None):
        """GET /api/markets/{firestore_doc_id}/"""
        market = fs.get(Collection.MARKETS, pk)
        if not market:
            return Response({"error": "Market not found"}, status=404)

        market["id"] = market.get("bayse_event_id", pk)
        market["time_remaining_hours"] = market.get("time_remaining", 0)

        # Attach latest quant metrics
        metrics = fs.query(
            Collection.QUANT_METRICS,
            filters=[("market_id", "==", pk)],
            order_by=("calculated_at", True),
            limit=1,
        )
        market["latest_quant_metrics"] = metrics[0] if metrics else None

        return Response(market)

    # ── scan ──────────────────────────────────────────────────────────
    @action(detail=False, methods=['post'])
    def scan(self, request):
        """POST /api/markets/scan/ — trigger Agent 01 market scanner"""
        try:
            max_results = int(request.data.get('max_results', 20))
            min_volume = float(request.data.get('min_volume', 0))
            min_liquidity = float(request.data.get('min_liquidity', 0))

            markets = scan_markets(
                max_results=max_results,
                min_volume=min_volume,
                min_liquidity=min_liquidity,
            )

            return Response({
                "success": True,
                "count": len(markets),
                "markets": markets,
                "scanned_at": timezone.now(),
            })
        except Exception as e:
            logger.error(f"Market scan failed: {e}")
            return Response({"success": False, "error": str(e)}, status=500)

    # ── analyze ───────────────────────────────────────────────────────
    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """POST /api/markets/{pk}/analyze/ — full 4-agent pipeline"""
        try:
            from agents.quant_analyzer import analyze_market
            from agents.ai_probability import estimate_probability

            market = fs.get(Collection.MARKETS, pk)
            if not market:
                return Response({"success": False, "error": "Market not found"}, status=404)

            user_bankroll = float(request.data.get('user_bankroll', 10000))

            # Sync latest market data
            market["id"] = market.get("bayse_event_id", pk)
            fs.set(Collection.MARKETS, pk, market, merge=True)

            # Agent 02: Quant
            quant_metrics = analyze_market(pk)

            # Agent 03: AI
            ai_result = estimate_probability(pk)

            # Agent 04: Signal
            signal_doc = generate_signal(market_event_id=pk, user_bankroll=user_bankroll)

            # Latest AI analysis
            latest_ai = fs.query(
                Collection.AI_ANALYSES,
                filters=[("market_id", "==", pk)],
                order_by=("analyzed_at", True),
                limit=1,
            )

            return Response({
                "success": True,
                "market": market,
                "quant_metrics": quant_metrics,
                "ai_analysis": latest_ai[0] if latest_ai else None,
                "signal": signal_doc,
                "analyzed_at": timezone.now(),
            })
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return Response({"success": False, "error": str(e)}, status=500)

    # ── top ───────────────────────────────────────────────────────────
    @action(detail=False, methods=['get'])
    def top(self, request):
        """GET /api/markets/top/?limit=10&category=crypto"""
        limit = int(request.query_params.get('limit', 20))
        category = request.query_params.get('category')

        markets = get_top_markets(limit=limit, category=category)

        # Deduplicate
        seen = set()
        unique = []
        for m in markets:
            eid = m.get("bayse_event_id")
            if eid not in seen:
                seen.add(eid)
                m["id"] = eid
                m["time_remaining_hours"] = m.get("time_remaining", 0)
                unique.append(m)

        return Response({"success": True, "count": len(unique), "markets": unique})

    # ── price_history ─────────────────────────────────────────────────
    @action(detail=False, methods=['get'])
    def price_history(self, request):
        """GET /api/markets/price_history/?event_id=..."""
        event_id = request.query_params.get('event_id')
        if not event_id:
            return Response({"error": "event_id required"}, status=400)
        try:
            history = bayse_client.get_price_history(event_id)
            return Response(history if history else [])
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    # ── order_book ────────────────────────────────────────────────────
    @action(detail=False, methods=['get'])
    def order_book(self, request):
        """GET /api/markets/order_book/?event_id=..."""
        event_id = request.query_params.get('event_id')
        if not event_id:
            return Response({"error": "event_id required"}, status=400)
        try:
            outcome_id = bayse_client.get_outcome_id(event_id)
            if not outcome_id:
                return Response({"error": "No active order book"}, status=404)
            ob = bayse_client.get_order_book(outcome_id)
            return Response(ob if ob else {})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    # ── async helpers ─────────────────────────────────────────────────
    @action(detail=False, methods=['post'])
    def scan_async(self, request):
        """POST /api/markets/scan_async/"""
        task = async_scan_markets.delay(
            status=request.data.get('status', 'open'),
            min_volume=request.data.get('min_volume', 0),
            min_liquidity=request.data.get('min_liquidity', 0),
            max_results=request.data.get('max_results', 50),
        )
        return Response({
            "success": True,
            "task_id": task.id,
            "status_url": f"/api/markets/task_status/{task.id}/",
        })

    @action(detail=True, methods=['post'])
    def analyze_async(self, request, pk=None):
        """POST /api/markets/{pk}/analyze_async/"""
        task = async_analyze_market.delay(
            market_id=pk,
            user_bankroll=request.data.get('user_bankroll', 10000),
        )
        return Response({
            "success": True,
            "task_id": task.id,
            "status_url": f"/api/markets/task_status/{task.id}/",
        })

    @action(detail=False, methods=['get'])
    def task_status(self, request):
        """GET /api/markets/task_status/?task_id=xxx"""
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response({"error": "task_id required"}, status=400)
        task = AsyncResult(task_id)
        return Response({
            "task_id": task_id,
            "status": task.status,
            "ready": task.ready(),
            "result": task.result if task.ready() else None,
            "error": str(task.info) if task.failed() else None,
        })
