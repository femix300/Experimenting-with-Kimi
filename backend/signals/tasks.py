"""
Background Signal Scanner Task.
Runs the full 4-agent pipeline on all active markets every 5 minutes.
"""
import logging
from celery import shared_task
from agents.market_scanner import scan_markets
from agents.quant_analyzer import QuantAnalyzerAgent
from agents.ai_probability import AIProbabilityAgent
from agents.signal_generator import SignalGeneratorAgent
from utils.firebase_client import FirebaseClient
from services.gemini_client import GeminiClient
from services.bayse_client import BayseClient

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def background_signal_scanner(self):
    """
    Run the full 4-agent pipeline on all active markets.
    This task is designed to be called every 5 minutes via Celery Beat.
    """
    logger.info("Starting background signal scanner...")

    try:
        # Step 1: Scan all active markets
        scan_result = scan_markets(
            status="open",
            max_results=50,
            min_volume=100
        )

        if not scan_result.get("success"):
            logger.error(f"Market scan failed: {scan_result.get('error')}")
            return {"status": "error", "message": scan_result.get("error")}

        markets = scan_result.get("markets", [])
        logger.info(f"Scanned {len(markets)} markets")

        # Initialize agents
        bayse_client = BayseClient()
        gemini_client = GeminiClient()
        firebase_client = FirebaseClient()

        quant_agent = QuantAnalyzerAgent(bayse_client, firebase_client)
        ai_agent = AIProbabilityAgent(gemini_client, firebase_client)
        signal_agent = SignalGeneratorAgent(firebase_client)

        signals_generated = 0

        # Step 2: Run pipeline on each market
        for market in markets[:20]:  # Limit to top 20 to stay within time budget
            try:
                event_id = market.get("bayse_event_id")
                if not event_id:
                    continue

                # Agent 02: Quant Analysis
                quant_result = quant_agent.analyze(event_id, market.get("title", ""))
                if not quant_result.get("success"):
                    continue

                # Agent 03: AI Probability
                ai_result = ai_agent.estimate(market.get("title", ""), {
                    "description": market.get("description", ""),
                    "category": market.get("category", "other"),
                })
                if not ai_result.get("success"):
                    continue

                # Agent 04: Generate Signal
                signal = signal_agent.generate(quant_result, ai_result)
                if signal and signal.get("is_active"):
                    signals_generated += 1
                    logger.info(f"Generated signal for {market.get('title', '')}: edge={signal.get('edge_score', 0):.1f}%")

            except Exception as e:
                logger.error(f"Pipeline error for market {market.get('id', 'unknown')}: {e}")
                continue

        logger.info(f"Background scanner complete. Generated {signals_generated} signals.")
        return {
            "status": "success",
            "markets_scanned": len(markets),
            "signals_generated": signals_generated,
        }

    except Exception as e:
        logger.error(f"Background scanner failed: {e}")
        # Retry via Celery
        try:
            self.retry(exc=e)
        except Exception:
            pass
        return {"status": "error", "message": str(e)}
