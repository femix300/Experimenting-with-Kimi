"""
Signals API Views (Firestore Refactored)
=========================================
Original: signals/views.py

Strategy:
- Django views now READ from Firestore (not SQLite) to serve API requests.
- Alternatively, you can make these views thin redirects telling the React frontend
  to listen to Firestore directly. But for backward compatibility during the hackathon,
  we keep the DRF response shape and read from Firestore here.

Changes:
- Replaced Signal.objects.filter()  ->  fs.query(Collection.SIGNALS, ...)
- Replaced Signal.objects.get()     ->  fs.get(Collection.SIGNALS, ...)
- Replaced aggregate queries        ->  Python aggregation on query results
- Kept serializer imports for type shape compatibility (data is now dict-based).

Migration: Replace signals/views.py with this file.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from django.utils import timezone
from utils.firebase_client import fs, Collection
from agents.signal_generator import get_active_signals, deactivate_expired_signals
import logging

logger = logging.getLogger(__name__)


class SignalViewSet(ViewSet):
    """
    Signal API endpoints backed by Firestore.
    All endpoints return the same JSON shape as before for React compatibility.
    """


    def _get_user_id(self, request):
        """Get the current user ID from the request."""
        return str(request.user.username) if request.user.is_authenticated else "anonymous"

    # ---------- list ----------
    def list(self, request):
        user_id = self._get_user_id(request)
        filters.append(("user_id", "==", user_id))
        """GET /api/signals/"""
        filters = []

        is_active = request.query_params.get('is_active', 'true')
        if is_active.lower() == 'true':
            filters.append(("is_active", "==", True))

        direction = request.query_params.get('direction')
        if direction:
            filters.append(("direction", "==", direction.upper()))

        min_edge = request.query_params.get('min_edge')
        if min_edge:
            filters.append(("edge_score", ">=", float(min_edge)))

        strength = request.query_params.get('strength')
        if strength:
            filters.append(("signal_strength", "==", strength))

        results = fs.query(
            collection=Collection.SIGNALS,
            filters=filters,
            order_by=("edge_score", True),
            limit=50,
        )
    def active(self, request):
        """GET /api/signals/active/"""
        limit = int(request.query_params.get("limit", 20))
        min_edge = float(request.query_params.get("min_edge", 0))
        signals = get_active_signals(limit=limit, min_edge=min_edge, user_id=self._get_user_id(request))
        
        # Enrich signals with market category
        for signal in signals:
            market_id = signal.get("market_event_id") or signal.get("market_id")
            if market_id:
                market = fs.get(Collection.MARKETS, market_id)
                if market:
                    signal["category"] = market.get("category", "other")
                else:
                    signal["category"] = "other"
            else:
                signal["category"] = "other"
        
        return Response({"success": True, "count": len(signals), "signals": signals})
    def retrieve(self, request, pk=None):
        """GET /api/signals/{id}/"""
        signal = fs.get(Collection.SIGNALS, pk)
        if not signal:
            return Response({"success": False, "error": "Signal not found"}, status=404)
        return Response({"success": True, "signal": signal})

    # ---------- cleanup ----------
    @action(detail=False, methods=['post'])
    def cleanup(self, request):
        """POST /api/signals/cleanup/"""
        try:
            count = deactivate_expired_signals()
            return Response({"success": True, "deactivated_count": count})
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return Response({"success": False, "error": str(e)}, status=500)


    # ---------- clear_all ----------
    @action(detail=False, methods=['post'])
    def clear_all(self, request):
        """POST /api/signals/clear_all/ — delete ALL signals from Firestore."""
        try:
            signals = fs.query(
                Collection.SIGNALS,
                filters=[("is_active", "==", True), ("user_id", "==", self._get_user_id(request))],
                limit=500,
            )
            deleted = 0
            for signal in signals:
                signal_id = signal.get("id") or signal.get("signal_id")
                if signal_id:
                    fs.delete(Collection.SIGNALS, signal_id)
                    deleted += 1
            
            # Also clear deactivated ones
            all_signals = fs.query(Collection.SIGNALS, limit=500)
            for signal in all_signals:
                signal_id = signal.get("id") or signal.get("signal_id")
                if signal_id:
                    fs.delete(Collection.SIGNALS, signal_id)
                    deleted += 1
            
            logger.info(f"Cleared {deleted} signals from Firestore")
            return Response({"success": True, "deleted_count": deleted})
        except Exception as e:
            logger.error(f"Clear all error: {e}")
            return Response({"success": False, "error": str(e)}, status=500)

    # ---------- stats ----------
    @action(detail=False, methods=['get'])
    def stats(self, request):
        user_id = self._get_user_id(request)
        """GET /api/signals/stats/"""
        active_signals = fs.query(
            Collection.SIGNALS,
            filters=[("is_active", "==", True), ("user_id", "==", user_id)],
        )

        stats = {
            "total_active": len(active_signals),
            "by_direction": {"BUY": 0, "SELL": 0, "WAIT": 0},
            "by_strength": {"strong": 0, "moderate": 0, "weak": 0},
            "edge_stats": {"avg_edge": 0, "max_edge": 0, "min_edge": 0},
            "confidence_stats": {"avg_confidence": 0, "max_confidence": 0, "min_confidence": 0},
        }

        if not active_signals:
            return Response({"success": True, "stats": stats})

        edges = [s.get("edge_score", 0) for s in active_signals]
        confs = [s.get("confidence", 0) for s in active_signals]

        for s in active_signals:
            d = s.get("direction", "WAIT")
            if d in stats["by_direction"]:
                stats["by_direction"][d] += 1
            st = s.get("signal_strength", "weak")
            if st in stats["by_strength"]:
                stats["by_strength"][st] += 1

        stats["edge_stats"] = {
            "avg_edge": round(sum(edges) / len(edges), 2),
            "max_edge": max(edges),
            "min_edge": min(edges),
        }
        stats["confidence_stats"] = {
            "avg_confidence": round(sum(confs) / len(confs), 2),
            "max_confidence": max(confs),
            "min_confidence": min(confs),
        }

        return Response({"success": True, "stats": stats})



    """
    Probability Calibration Dashboard Feature
    """
    @action(detail=False, methods=['get'])
    def calibration_curve(self, request):
        """
        Get calibration curve data (predicted probability vs actual outcome frequency)
        GET /api/signals/calibration-curve/
        
        This shows how accurate the AI's probability estimates are.
        Perfect calibration means when AI says 70%, outcomes happen 70% of the time.
        """
        try:
            # Get resolved markets with AI predictions
            resolved_markets = fs.query(
                collection=Collection.MARKETS,
                filters=[("status", "==", "resolved")],
                limit=200
            )
            
            # Create bins for probability ranges (0-10%, 10-20%, etc.)
            bins = [i for i in range(0, 101, 10)]
            bin_data = {}
            for b in bins[:-1]:
                bin_data[f"{b}-{b+10}%"] = {"count": 0, "wins": 0}
            
            for market in resolved_markets:
                # Get AI analysis for this market
                ai_analyses = fs.query(
                    collection=Collection.AI_ANALYSES,
                    filters=[("market_id", "==", market.get('bayse_event_id'))],
                    order_by=("analyzed_at", True),
                    limit=1
                )
                
                if not ai_analyses:
                    continue
                
                ai = ai_analyses[0]
                predicted = ai.get('probability', 50)
                actual = market.get('resolution', '').upper()
                
                # Determine which bin this prediction falls into
                bin_index = min(int(predicted / 10), 9)
                bin_key = f"{bin_index * 10}-{(bin_index + 1) * 10}%"
                
                bin_data[bin_key]["count"] += 1
                if actual == "YES":
                    bin_data[bin_key]["wins"] += 1
            
            # Calculate actual probabilities for each bin
            calibration_points = []
            for bin_key, data in bin_data.items():
                if data["count"] > 0:
                    actual_prob = (data["wins"] / data["count"]) * 100
                    calibration_points.append({
                        "bin": bin_key,
                        "predicted": float(bin_key.split("-")[0]) + 5,
                        "actual": round(actual_prob, 1),
                        "count": data["count"]
                    })
            
            # Create perfect line for reference (predicted = actual)
            perfect_line = [{"predicted": i, "actual": i} for i in range(0, 101, 10)]
            
            return Response({
                "success": True,
                "calibration_points": calibration_points,
                "perfect_line": perfect_line,
                "total_markets_analyzed": sum(d["count"] for d in bin_data.values())
            })
            
        except Exception as e:
            logger.error(f"Error generating calibration curve: {e}")
            return Response({"success": False, "error": str(e)}, status=500)


    @action(detail=False, methods=['get'])
    def accuracy_metrics(self, request):
        """
        Get overall AI prediction accuracy metrics
        GET /api/signals/accuracy-metrics/
        
        Returns: accuracy, Brier score, log loss, calibration error
        """
        try:
            import math
            
            resolved_markets = fs.query(
                collection=Collection.MARKETS,
                filters=[("status", "==", "resolved")],
                limit=200
            )
            
            total = 0
            correct = 0
            brier_score = 0
            log_loss = 0
            calibration_error = 0
            
            # For calibration error, we need bin data
            bins = [i for i in range(0, 101, 10)]
            bin_data = {f"{b}-{b+10}%": {"count": 0, "wins": 0} for b in bins[:-1]}
            
            for market in resolved_markets:
                ai_analyses = fs.query(
                    collection=Collection.AI_ANALYSES,
                    filters=[("market_id", "==", market.get('bayse_event_id'))],
                    order_by=("analyzed_at", True),
                    limit=1
                )
                
                if not ai_analyses:
                    continue
                
                ai = ai_analyses[0]
                predicted = ai.get('probability', 50) / 100
                actual = 1 if market.get('resolution', '').upper() == "YES" else 0
                
                total += 1
                
                # Accuracy: did the AI get the direction right?
                if (predicted > 0.5 and actual == 1) or (predicted < 0.5 and actual == 0):
                    correct += 1
                
                # Brier Score: mean squared error (lower is better, 0 = perfect)
                brier_score += (predicted - actual) ** 2
                
                # Log Loss: penalizes confident wrong predictions (lower is better)
                if actual == 1:
                    log_loss += -math.log(max(predicted, 0.01))
                else:
                    log_loss += -math.log(max(1 - predicted, 0.01))
                
                # For calibration error, track bins
                bin_index = min(int(predicted * 10), 9)
                bin_key = f"{bin_index * 10}-{(bin_index + 1) * 10}%"
                bin_data[bin_key]["count"] += 1
                if actual == 1:
                    bin_data[bin_key]["wins"] += 1
            
            # Calculate final metrics
            if total > 0:
                accuracy = (correct / total) * 100
                brier_score = brier_score / total
                log_loss = log_loss / total
                
                # Calibration Error: average difference between predicted and actual
                calibration_error_sum = 0
                bin_count = 0
                for bin_key, data in bin_data.items():
                    if data["count"] > 0:
                        predicted_bin = float(bin_key.split("-")[0]) + 5
                        actual_bin = (data["wins"] / data["count"]) * 100
                        calibration_error_sum += abs(predicted_bin - actual_bin) * data["count"]
                        bin_count += data["count"]
                calibration_error = calibration_error_sum / bin_count if bin_count > 0 else 0
            else:
                accuracy = 0
                brier_score = 0
                log_loss = 0
                calibration_error = 0
            
            return Response({
                "success": True,
                "metrics": {
                    "total_predictions": total,
                    "accuracy": round(accuracy, 1),
                    "brier_score": round(brier_score, 4),
                    "log_loss": round(log_loss, 4),
                    "calibration_error": round(calibration_error, 1),
                    "perfect_accuracy": 100,
                    "perfect_brier": 0,
                    "perfect_log_loss": 0,
                    "perfect_calibration_error": 0
                }
            })
            
        except Exception as e:
            logger.error(f"Error calculating accuracy: {e}")
            return Response({"success": False, "error": str(e)}, status=500)


    @action(detail=False, methods=['get'])
    def resolved_markets(self, request):
        """
        Get resolved markets with AI predictions for detailed calibration view
        GET /api/signals/resolved-markets/
        
        Query params: limit (default 50)
        """
        try:
            limit = int(request.query_params.get('limit', 50))
            
            resolved_markets = fs.query(
                collection=Collection.MARKETS,
                filters=[("status", "==", "resolved")],
                limit=limit
            )
            
            results = []
            for market in resolved_markets:
                # Get AI analysis
                ai_analyses = fs.query(
                    collection=Collection.AI_ANALYSES,
                    filters=[("market_id", "==", market.get('bayse_event_id'))],
                    order_by=("analyzed_at", True),
                    limit=1
                )
                
                market_data = {
                    "market_id": market.get('bayse_event_id'),
                    "market_title": market.get('title', 'Unknown'),
                    "actual_outcome": market.get('resolution', 'unknown'),
                    "resolved_at": market.get('resolved_at')
                }
                
                if ai_analyses:
                    ai = ai_analyses[0]
                    market_data["predicted_probability"] = ai.get('probability', 50)
                    market_data["confidence"] = ai.get('confidence', 50)
                    market_data["reasoning"] = ai.get('reasoning', '')[:200]
                    market_data["analyzed_at"] = ai.get('analyzed_at')
                    market_data["was_correct"] = (
                        (ai.get('probability', 50) > 50 and market.get('resolution', '').upper() == "YES") or
                        (ai.get('probability', 50) < 50 and market.get('resolution', '').upper() == "NO")
                    )
                
                results.append(market_data)
            
            return Response({
                "success": True,
                "count": len(results),
                "markets": results
            })
            
        except Exception as e:
            logger.error(f"Error fetching resolved markets: {e}")
            return Response({"success": False, "error": str(e)}, status=500)