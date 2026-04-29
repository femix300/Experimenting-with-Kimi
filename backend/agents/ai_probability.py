"""
Agent 03: AI Probability Agent (Firestore Refactored)
======================================================
Original: agents/ai_probability.py

Changes made:
- Replaced Market.objects.get()       ->  fs.get(Collection.MARKETS, ...)
- Replaced AIAnalysis.objects.create() ->  fs.set(Collection.AI_ANALYSES, ...)
- Input market_id is now the Firestore doc ID (bayse_event_id).
- Returns dict with AI analysis result + Firestore doc ID.
- Now properly captures and stores the actual Gemini model used (after auto-failover)
- Uses original field names (probability, confidence, reasoning, sources) for frontend compatibility
"""

from services.gemini_client import gemini_client
from utils.firebase_client import fs, Collection
import logging

logger = logging.getLogger(__name__)


def estimate_probability(market_event_id: str, market_context: dict | None = None):
    """
    Use Gemini AI to estimate true probability of a market outcome.
    Reads market from Firestore, writes AIAnalysis back to Firestore.

    Args:
        market_event_id: Firestore doc ID (= bayse_event_id)
        market_context: Optional pre-fetched market data dict

    Returns:
        Dict with probability, confidence, reasoning + firestore_doc_id
    """
    try:
        # --- Read market from Firestore ---
        if market_context:
            market = market_context
        else:
            market = fs.get(Collection.MARKETS, market_event_id)

        if not market:
            logger.error(f"Market {market_event_id} not found in Firestore")
            raise ValueError(f"Market {market_event_id} not found")

        title = market.get("title", "Unknown")
        description = market.get("description", "")
        logger.info(f"Estimating probability for: {title}")

        if not market_context:
            market_context = {
                "current_price": float(market.get("current_price", 0)),
                "implied_probability": float(market.get("implied_probability", 0)),
                "volume_24h": float(market.get("volume_24h", 0)),
            }

        # Call Gemini - this now returns the actual model used in result['model_used']
        result = gemini_client.estimate_probability(
            event_title=title,
            event_description=description,
            market_context=market_context,
        )

        # Debug logging - show which model was actually used
        actual_model = result.get('model_used', 'unknown')
        logger.info(f"AI Result using model: {actual_model}")
        logger.info(f"AI Result: probability={result.get('probability')}, confidence={result.get('confidence')}")

        # Save AI analysis to Firestore (includes the actual model used)
        doc_id = save_ai_analysis(market_event_id, title, result, actual_model)

        # Debug logging
        logger.info(f"AI Analysis saved to Firestore with ID: {doc_id}")

        logger.info(f"AI Probability: {result['probability']}% (Confidence: {result['confidence']}%) using {actual_model}")
        logger.info(f"Reasoning: {result.get('reasoning', 'N/A')[:200]}...")

        return {
            **result,
            "firestore_doc_id": doc_id,
            "market_event_id": market_event_id,
            "model_used": actual_model,
        }

    except Exception as e:
        logger.exception(f"Error estimating probability for {market_event_id}: {e}")
        raise


def save_ai_analysis(market_event_id: str, market_title: str, result: dict, model_used: str = None) -> str:
    """
    Save AI analysis to Firestore. Document ID includes timestamp for history.
    Returns the Firestore doc ID.

    Uses original field names for frontend compatibility.
    """
    try:
        from django.utils import timezone
        now = timezone.now()
        doc_id = f"{market_event_id}_{now.isoformat()}"

        # Use the actual model passed from estimate_probability, or fallback
        actual_model = model_used or result.get("model_used", "gemini-flash-latest")

        doc = {
            "market_id": market_event_id,
            "market_title": market_title,
            "probability": result.get("probability", 50),           # Original field name
            "confidence": result.get("confidence", 0),              # Original field name
            "reasoning": result.get("reasoning", ""),               # Original field name
            "sources": result.get("sources_consulted", ""),         # Original field name
            "model_used": actual_model,
            "search_grounding_used": result.get("search_grounding", True),
            "analyzed_at": now,
        }

        fs.set(Collection.AI_ANALYSES, doc_id, doc)
        logger.info(f"Saved AI analysis with model {actual_model}: {doc_id}")
        return doc_id

    except Exception as e:
        logger.error(f"Error saving AI analysis: {e}")
        return ""


def get_latest_ai_analysis(market_event_id: str) -> dict | None:
    """
    Get the most recent AI analysis for a market from Firestore.
    Returns dict with original field names.
    """
    results = fs.query(
        collection=Collection.AI_ANALYSES,
        filters=[("market_id", "==", market_event_id)],
        order_by=("analyzed_at", True),
        limit=1,
    )
    if results:
        # Ensure field names are original format
        doc = results[0]
        return {
            "probability": doc.get("probability", 50),
            "confidence": doc.get("confidence", 0),
            "reasoning": doc.get("reasoning", ""),
            "sources": doc.get("sources", ""),
            "model_used": doc.get("model_used", ""),
            "analyzed_at": doc.get("analyzed_at"),
            "market_id": doc.get("market_id"),
            "market_title": doc.get("market_title"),
        }
    return None