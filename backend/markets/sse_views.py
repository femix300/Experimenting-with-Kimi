"""
SSE Streaming endpoint for real-time pipeline progress.
Each agent completion sends an SSE event to the frontend.
"""
import json
import time
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from utils.firebase_client import fs, Collection
import logging

logger = logging.getLogger(__name__)


def analyze_stream(market_event_id, user_id="anonymous", user_bankroll=10000):
    """
    Generator that yields SSE events as each agent completes.
    Final event contains the full analysis result.
    """
    from agents.quant_analyzer import analyze_market
    from agents.ai_probability import estimate_probability
    from agents.signal_generator import generate_signal

    try:
        # 1. Fetch market
        market = fs.get(Collection.MARKETS, market_event_id)
        if not market:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Market not found'})}\n\n"
            return

        market["id"] = market.get("bayse_event_id", market_event_id)
        fs.set(Collection.MARKETS, market_event_id, market, merge=True)
        market_title = market.get('title', 'Unknown')

        # Agent 01: Market Scanner (already done — market was fetched)
        yield f"data: {json.dumps({'type': 'progress', 'step': 'scanner', 'agent': 1, 'total': 4, 'message': 'Market data loaded'})}\n\n"

        # Agent 02: Quant Analyzer
        yield f"data: {json.dumps({'type': 'progress', 'step': 'quant', 'agent': 2, 'total': 4, 'message': 'Running quantitative analysis...'})}\n\n"
        try:
            quant_metrics = analyze_market(market_event_id)
        except Exception as e:
            logger.error(f"Quant analysis failed: {e}")
            quant_metrics = {
                'momentum_score': 0, 'momentum_direction': 'neutral',
                'price_change_1h': 0, 'price_change_6h': 0, 'price_change_24h': 0,
                'volume_acceleration': 1.0, 'volume_trend': 'stable',
                'bid_ask_spread': 0, 'order_book_bias': 'neutral',
                'bid_depth': 0, 'ask_depth': 0,
            }
        yield f"data: {json.dumps({'type': 'progress', 'step': 'quant_complete', 'agent': 2, 'total': 4, 'message': 'Quant analysis complete'})}\n\n"

        # Agent 03: AI Probability
        yield f"data: {json.dumps({'type': 'progress', 'step': 'ai', 'agent': 3, 'total': 4, 'message': 'Querying Gemini AI...'})}\n\n"
        try:
            ai_result = estimate_probability(market_event_id)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            ai_result = {
                'probability': 50, 'confidence': 0,
                'reasoning': 'AI analysis unavailable',
                'sources': '', 'model_used': 'fallback',
            }
        yield f"data: {json.dumps({'type': 'progress', 'step': 'ai_complete', 'agent': 3, 'total': 4, 'message': 'AI probability estimation complete'})}\n\n"

        # Agent 04: Signal Generator
        yield f"data: {json.dumps({'type': 'progress', 'step': 'signal', 'agent': 4, 'total': 4, 'message': 'Generating trade signals...'})}\n\n"
        try:
            logger.info(f"SSE generating signal for user_id={user_id}")
            signal_doc = generate_signal(market_event_id=market_event_id, user_id=user_id, user_bankroll=user_bankroll)
        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            signal_doc = None
        yield f"data: {json.dumps({'type': 'progress', 'step': 'signal_complete', 'agent': 4, 'total': 4, 'message': 'Signal generation complete'})}\n\n"

        # Fetch latest AI analysis
        latest_ai = fs.query(
            Collection.AI_ANALYSES,
            filters=[("market_id", "==", market_event_id)],
            order_by=("analyzed_at", True),
            limit=1,
        )

        # Final result
        result = {
            "type": "complete",
            "success": True,
            "market": market,
            "quant_metrics": quant_metrics,
            "ai_analysis": latest_ai[0] if latest_ai else None,
            "signal": signal_doc,
            "analyzed_at": timezone.now().isoformat(),
        }
        yield f"data: {json.dumps(result, default=str)}\n\n"

    except Exception as e:
        logger.exception(f"Streaming analysis failed: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@csrf_exempt
def sse_analyze_view(request, pk=None):
    print("sse_analyze_view CALLED", flush=True)
    # Extract Firebase UID from Authorization header
    user_id = "anonymous"
    auth_header = request.headers.get("Authorization", "")
    print("SSE Auth header:", auth_header[:50] if auth_header else "NONE", flush=True)
    if auth_header.startswith("Bearer "):
        try:
            from firebase_admin import auth as firebase_auth
            token = auth_header[7:]
            decoded = firebase_auth.verify_id_token(token, check_revoked=False)
            user_id = decoded.get("uid", "anonymous")
            print(f"SSE Firebase auth SUCCESS: uid={user_id}", flush=True)
        except Exception as e:
            print(f"SSE Firebase auth ERROR: {e}", flush=True)
    """
    View that returns a StreamingHttpResponse for SSE.
    """
    user_bankroll = 10000
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            user_bankroll = float(body.get('user_bankroll', 10000))
        except Exception as e:
            logger.error(f"SSE Firebase auth failed: {e}")
            pass

    response = StreamingHttpResponse(
        analyze_stream(pk, user_id, user_bankroll),
        content_type='text/event-stream',
        status=200
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    response['Access-Control-Allow-Origin'] = '*'
    return response
