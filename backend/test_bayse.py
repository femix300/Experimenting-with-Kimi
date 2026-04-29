"""
Test script for all 4 agents
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from agents.market_scanner import scan_markets
from agents.signal_generator import run_full_analysis_pipeline
from markets.models import Market

def test_full_pipeline():
    """Test the complete 4-agent pipeline"""
    print("=" * 60)
    print("TESTING COMPLETE 4-AGENT PIPELINE")
    print("=" * 60)
    
    # Step 1: Scan markets
    print("\n1️⃣ AGENT 01: Market Scanner")
    print("-" * 60)
    markets = scan_markets(max_results=5)
    print(f"✅ Scanned {len(markets)} markets")
    
    if not markets:
        print("❌ No markets found. Check Bayse API configuration.")
        return
    
    # Pick the top market
    top_market = markets[0]
    print(f"\n📊 Analyzing: {top_market.title}")
    print(f"   Current Price: ₦{top_market.current_price}")
    print(f"   Implied Probability: {top_market.implied_probability}%")
    
    # Step 2-4: Run full analysis pipeline
    print(f"\n2️⃣ 3️⃣ 4️⃣ Running Full Analysis Pipeline...")
    print("-" * 60)
    
    try:
        result = run_full_analysis_pipeline(
            market_id=top_market.id,
            user_bankroll=10000
        )
        
        # Display results
        print("\n📊 QUANT METRICS:")
        quant = result['quant_metrics']
        print(f"   Momentum: {quant['momentum_score']} ({quant['momentum_direction']})")
        print(f"   Volume Acceleration: {quant['volume_acceleration']}x")
        print(f"   Order Book Bias: {quant['order_book_bias']}")
        
        print("\n🤖 AI ANALYSIS:")
        ai = result['ai_analysis']
        print(f"   AI Probability: {ai['probability']}%")
        print(f"   Confidence: {ai['confidence']}%")
        print(f"   Reasoning: {ai['reasoning']}")
        
        print("\n💡 SIGNAL:")
        signal = result['signal']
        if signal:
            print(f"   Direction: {signal.direction}")
            print(f"   Edge Score: {signal.edge_score}%")
            print(f"   Expected Value: ₦{signal.expected_value}")
            print(f"   Kelly Stakes:")
            print(f"     - Conservative: ₦{signal.recommended_stake_conservative}")
            print(f"     - Balanced: ₦{signal.recommended_stake_balanced}")
            print(f"     - Aggressive: ₦{signal.recommended_stake_aggressive}")
        else:
            print("   No signal generated (edge too small)")
        
        print("\n" + "=" * 60)
        print("✅ PIPELINE TEST COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Pipeline error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_full_pipeline()