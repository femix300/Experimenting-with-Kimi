"""
Test the fixed market scanner
"""
import os
import sys

# Set Django settings FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Import and setup Django
import django
django.setup()

# NOW safe to import Django models
from agents.market_scanner import scan_markets
from markets.models import Market


def test_scanner():
    print("=" * 70)
    print("TESTING FIXED MARKET SCANNER")
    print("=" * 70)
    
    # Scan with very low thresholds
    markets = scan_markets(
        status='open',
        min_volume=0,
        min_liquidity=0,
        max_results=10
    )
    
    print(f"\n✅ Scan complete!")
    print(f"   Found {len(markets)} markets\n")
    
    # Check database
    all_markets = Market.objects.all()
    print(f"📊 Database Status:")
    print(f"   Total markets: {all_markets.count()}")
    
    if all_markets.exists():
        print(f"\n📋 Markets in database:")
        for m in all_markets[:10]:
            print(f"   • {m.title}")
            print(f"     Price: ₦{m.current_price} | Volume: {m.total_volume} | Liquidity: {m.liquidity}")
            print()
    else:
        print("\n⚠️  No markets found in database")
        print("    Possible reasons:")
        print("    1. Bayse API returned no events")
        print("    2. All events were filtered out")
        print("    3. API credentials are incorrect")
        print("\n    Check the logs above for details")


if __name__ == '__main__':
    test_scanner()