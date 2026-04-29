"""
Celery tasks for market operations
"""
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def async_scan_markets(status='open', min_volume=0, min_liquidity=0, max_results=50):
    """
    Run market scanner in background
    """
    from agents.market_scanner import scan_markets
    
    logger.info(f"Starting background market scan (status={status})...")
    
    try:
        result = scan_markets(
            status=status,
            min_volume=min_volume,
            min_liquidity=min_liquidity,
            max_results=max_results
        )
        
        cache.set('last_scan_result', result, 300)
        cache.set('last_scan_time', str(timezone.now()), 300)
        
        logger.info(f"Background scan complete: {len(result)} markets found")
        return {'markets_found': len(result), 'status': 'success'}
        
    except Exception as e:
        logger.error(f"Background scan failed: {str(e)}")
        return {'markets_found': 0, 'status': 'error', 'error': str(e)}


@shared_task
def async_analyze_market(market_id, user_bankroll=10000):
    """
    Run full analysis pipeline in background
    """
    from agents.signal_generator import run_full_analysis_pipeline
    
    logger.info(f"Starting background analysis for market {market_id}...")
    
    try:
        result = run_full_analysis_pipeline(market_id, user_bankroll)
        
        cache_key = f"analysis_result_{market_id}"
        cache.set(cache_key, result, 3600)
        
        logger.info(f"Background analysis complete for market {market_id}")
        return {'market_id': market_id, 'status': 'success', 'result': result}
        
    except Exception as e:
        logger.error(f"Background analysis failed for market {market_id}: {str(e)}")
        return {'market_id': market_id, 'status': 'error', 'error': str(e)}


@shared_task
def periodic_market_scan():
    """
    Run every 5 minutes to keep markets fresh
    """
    from agents.market_scanner import scan_markets
    
    logger.info("Periodic market scan started...")
    
    try:
        result = scan_markets(status='open', max_results=50)
        logger.info(f"Periodic scan complete: {len(result)} markets")
        return {'markets_found': len(result), 'timestamp': str(timezone.now())}
        
    except Exception as e:
        logger.error(f"Periodic scan failed: {str(e)}")
        return {'markets_found': 0, 'error': str(e)}
