"""
Test API endpoints
"""
import requests
import json

BASE_URL = 'http://127.0.0.1:8000/api'


def test_markets_api():
    """Test markets endpoints"""
    print("\n" + "="*60)
    print("TESTING MARKETS API")
    print("="*60)

    # Test 1: Scan markets
    print("\n1. POST /api/markets/scan/")
    response = requests.post(f"{BASE_URL}/markets/scan/", json={
        'max_results': 5,
        'min_volume': 1000
    })
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Scanned: {data.get('count', 0)} markets")

    # Test 2: List markets
    print("\n2. GET /api/markets/")
    response = requests.get(f"{BASE_URL}/markets/")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Markets: {data.get('count', 0)}")

    if data.get('results'):
        market_id = data['results'][0]['id']

        # Test 3: Analyze market
        print(f"\n3. POST /api/markets/{market_id}/analyze/")
        response = requests.post(f"{BASE_URL}/markets/{market_id}/analyze/", json={
            'user_bankroll': 10000
        })
        print(f"Status: {response.status_code}")
        analysis = response.json()

        if analysis.get('success'):
            print(f"✅ Analysis complete")
            if analysis.get('signal'):
                print(f"   Signal: {analysis['signal']['direction']}")
                print(f"   Edge: {analysis['signal']['edge_score']}%")


def test_signals_api():
    """Test signals endpoints"""
    print("\n" + "="*60)
    print("TESTING SIGNALS API")
    print("="*60)

    # Test 1: Get active signals
    print("\n1. GET /api/signals/active/")
    response = requests.get(f"{BASE_URL}/signals/active/")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Active signals: {data.get('count', 0)}")

    # Test 2: Get stats
    print("\n2. GET /api/signals/stats/")
    response = requests.get(f"{BASE_URL}/signals/stats/")
    print(f"Status: {response.status_code}")
    stats = response.json().get('stats', {})
    print(f"Total active: {stats.get('total_active', 0)}")


def test_portfolio_api():
    """Test portfolio endpoints"""
    print("\n" + "="*60)
    print("TESTING PORTFOLIO API")
    print("="*60)

    # Test 1: Get profile
    print("\n1. GET /api/portfolio/profile/")
    response = requests.get(f"{BASE_URL}/portfolio/profile/")
    print(f"Status: {response.status_code}")
    profile = response.json().get('profile', {})
    print(f"Bankroll: ₦{profile.get('bankroll', 0)}")
    print(f"Win Rate: {profile.get('win_rate', 0)}%")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("EdgeIQ Backend - API Tests")
    print("="*60)

    try:
        test_markets_api()
        test_signals_api()
        test_portfolio_api()

        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETE")
        print("="*60 + "\n")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server")
        print("Make sure Django is running: python manage.py runserver")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
