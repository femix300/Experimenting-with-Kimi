# EdgeIQ Backend

Django backend for EdgeIQ - prediction market trading signals with AI agents.

## Table of Contents
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Testing Endpoints](#testing-endpoints)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Admin Panel](#admin-panel)
- [Common Commands](#common-commands)

---

## Quick Start

### 1. Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
BAYSE_API_KEY=your_bayse_key_here
GEMINI_API_KEY=your_gemini_key_here
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 4. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 5. Run Server

```bash
python manage.py runserver
```

Server will be available at: `http://127.0.0.1:8000/`

---

## API Endpoints

### Markets Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/markets/scan/` | Fetch markets from Bayse |
| POST | `/api/markets/{id}/analyze/` | Run all 4 agents on a market |
| GET | `/api/markets/` | List all markets |
| GET | `/api/markets/{id}/` | Get specific market details |
| DELETE | `/api/markets/{id}/` | Delete a market |

### Signals Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/signals/` | List all signals |
| GET | `/api/signals/active/` | Get active trading signals |
| GET | `/api/signals/{id}/` | Get specific signal details |
| PATCH | `/api/signals/{id}/` | Update a signal |

### Portfolio Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/portfolio/profile/` | Get user profile |
| POST | `/api/portfolio/simulate_trade/` | Record a trade |
| GET | `/api/portfolio/analytics/` | Get performance metrics |
| GET | `/api/portfolio/trades/` | List all trades |
| GET | `/api/portfolio/positions/` | Get current positions |

### Backtesting Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/backtesting/run/` | Run backtest on strategy |
| GET | `/api/backtesting/results/` | Get backtest results |

---

## Testing Endpoints

### Using cURL

#### 1. Scan Markets from Bayse

```bash
curl -X POST http://127.0.0.1:8000/api/markets/scan/ \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "status": "success",
  "markets_scanned": 25,
  "message": "Markets successfully fetched from Bayse"
}
```

---

#### 2. List All Markets

```bash
curl -X GET http://127.0.0.1:8000/api/markets/ \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "count": 25,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Will Bitcoin reach $100,000 by end of 2024?",
      "description": "Prediction market for BTC price",
      "current_price": 0.65,
      "volume_24h": 150000,
      "created_at": "2024-04-19T10:30:00Z",
      "closes_at": "2024-12-31T23:59:59Z"
    }
  ]
}
```

---

#### 3. Get Specific Market

```bash
curl -X GET http://127.0.0.1:8000/api/markets/1/ \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "id": 1,
  "title": "Will Bitcoin reach $100,000 by end of 2024?",
  "description": "Prediction market for BTC price",
  "current_price": 0.65,
  "volume_24h": 150000,
  "momentum_score": 0.72,
  "volatility": 0.15,
  "created_at": "2024-04-19T10:30:00Z",
  "closes_at": "2024-12-31T23:59:59Z",
  "price_history": [...]
}
```

---

#### 4. Analyze Market (Run All 4 Agents)

```bash
curl -X POST http://127.0.0.1:8000/api/markets/1/analyze/ \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "status": "success",
  "market_id": 1,
  "analysis": {
    "quant_analysis": {
      "momentum_score": 0.72,
      "volume_trend": "increasing",
      "volatility": 0.15
    },
    "ai_probability": {
      "estimated_probability": 0.68,
      "confidence_level": "high",
      "reasoning": "Strong upward trend with high volume"
    },
    "signal_generated": {
      "signal_id": 5,
      "recommendation": "BUY",
      "edge": 0.18,
      "kelly_fraction": 0.12,
      "position_size": 0.06
    }
  }
}
```

---

#### 5. Get Active Signals

```bash
curl -X GET http://127.0.0.1:8000/api/signals/active/ \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "count": 8,
  "results": [
    {
      "id": 5,
      "market_id": 1,
      "market_title": "Will Bitcoin reach $100,000 by end of 2024?",
      "signal_type": "BUY",
      "edge": 0.18,
      "estimated_probability": 0.68,
      "current_price": 0.65,
      "recommended_size": 0.06,
      "kelly_fraction": 0.12,
      "status": "active",
      "created_at": "2024-04-19T12:00:00Z",
      "expires_at": "2024-04-20T12:00:00Z"
    }
  ]
}
```

---

#### 6. Get User Profile

```bash
curl -X GET http://127.0.0.1:8000/api/portfolio/profile/ \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "user_id": 1,
  "username": "trader_001",
  "portfolio_value": 10500.00,
  "cash_balance": 5000.00,
  "total_positions": 8,
  "total_return": 5.0,
  "risk_tolerance": "balanced",
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

#### 7. Simulate Trade

```bash
curl -X POST http://127.0.0.1:8000/api/portfolio/simulate_trade/ \
  -H "Content-Type: application/json" \
  -d '{
    "market_id": 1,
    "position_type": "BUY",
    "amount": 500.00,
    "price": 0.65
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "trade_id": 42,
  "market_id": 1,
  "position_type": "BUY",
  "amount": 500.00,
  "price": 0.65,
  "shares": 769.23,
  "timestamp": "2024-04-19T14:30:00Z",
  "new_cash_balance": 4500.00,
  "new_portfolio_value": 10500.00
}
```

---

#### 8. Get Portfolio Analytics

```bash
curl -X GET http://127.0.0.1:8000/api/portfolio/analytics/ \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "total_trades": 25,
  "winning_trades": 18,
  "losing_trades": 7,
  "win_rate": 0.72,
  "total_return": 5.0,
  "total_pnl": 500.00,
  "sharpe_ratio": 1.45,
  "max_drawdown": -0.08,
  "average_trade_size": 450.00,
  "best_trade": {
    "market_title": "Will Bitcoin reach $100,000?",
    "pnl": 150.00,
    "return": 30.0
  },
  "worst_trade": {
    "market_title": "Will Ethereum flip Bitcoin?",
    "pnl": -75.00,
    "return": -15.0
  }
}
```

---

#### 9. Get All Trades

```bash
curl -X GET http://127.0.0.1:8000/api/portfolio/trades/ \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "count": 25,
  "results": [
    {
      "id": 42,
      "market_id": 1,
      "market_title": "Will Bitcoin reach $100,000 by end of 2024?",
      "position_type": "BUY",
      "entry_price": 0.65,
      "exit_price": null,
      "amount": 500.00,
      "shares": 769.23,
      "pnl": null,
      "status": "open",
      "created_at": "2024-04-19T14:30:00Z",
      "closed_at": null
    }
  ]
}
```

---

#### 10. Get Current Positions

```bash
curl -X GET http://127.0.0.1:8000/api/portfolio/positions/ \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "count": 8,
  "total_value": 5500.00,
  "results": [
    {
      "market_id": 1,
      "market_title": "Will Bitcoin reach $100,000 by end of 2024?",
      "position_type": "BUY",
      "shares": 769.23,
      "entry_price": 0.65,
      "current_price": 0.68,
      "current_value": 523.08,
      "cost_basis": 500.00,
      "unrealized_pnl": 23.08,
      "unrealized_return": 4.62
    }
  ]
}
```

---

### Using Postman

1. **Import Collection**: Create a new collection called "EdgeIQ API"

2. **Set Base URL**: Create an environment variable
   - Variable: `base_url`
   - Value: `http://127.0.0.1:8000`

3. **Test Each Endpoint**: For each endpoint above, create a request:
   - **Name**: Descriptive name (e.g., "Scan Markets")
   - **Method**: GET/POST as specified
   - **URL**: `{{base_url}}/api/markets/scan/`
   - **Headers**: 
     - `Content-Type: application/json`
   - **Body** (for POST requests): Raw JSON

4. **Example Postman Request for Simulate Trade**:
   ```
   Method: POST
   URL: {{base_url}}/api/portfolio/simulate_trade/
   Headers:
     Content-Type: application/json
   Body (raw JSON):
   {
     "market_id": 1,
     "position_type": "BUY",
     "amount": 500.00,
     "price": 0.65
   }
   ```

---

### Using Python Requests

Create a test script `test_endpoints.py`:

```python
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_scan_markets():
    """Test market scanning endpoint"""
    url = f"{BASE_URL}/api/markets/scan/"
    response = requests.post(url)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_get_markets():
    """Test get all markets endpoint"""
    url = f"{BASE_URL}/api/markets/"
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_analyze_market(market_id):
    """Test market analysis endpoint"""
    url = f"{BASE_URL}/api/markets/{market_id}/analyze/"
    response = requests.post(url)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_get_active_signals():
    """Test get active signals endpoint"""
    url = f"{BASE_URL}/api/signals/active/"
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_simulate_trade():
    """Test simulate trade endpoint"""
    url = f"{BASE_URL}/api/portfolio/simulate_trade/"
    data = {
        "market_id": 1,
        "position_type": "BUY",
        "amount": 500.00,
        "price": 0.65
    }
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_get_analytics():
    """Test get analytics endpoint"""
    url = f"{BASE_URL}/api/portfolio/analytics/"
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("=== Testing EdgeIQ API Endpoints ===\n")
    
    print("1. Scanning Markets...")
    test_scan_markets()
    
    print("\n2. Getting All Markets...")
    test_get_markets()
    
    print("\n3. Analyzing Market ID 1...")
    test_analyze_market(1)
    
    print("\n4. Getting Active Signals...")
    test_get_active_signals()
    
    print("\n5. Simulating Trade...")
    test_simulate_trade()
    
    print("\n6. Getting Analytics...")
    test_get_analytics()
```

Run the test script:
```bash
python test_endpoints.py
```

---

## Project Structure

```
backend/
├── agents/                    # 4 AI agents
│   ├── market_scanner.py      # Fetches markets from Bayse
│   ├── quant_analyzer.py      # Momentum & volume analysis
│   ├── ai_probability.py      # Gemini AI probability estimates
│   └── signal_generator.py    # Generates trading signals
├── markets/                   # Market data models & views
│   ├── models.py              # Market, PriceHistory models
│   ├── views.py               # API views for markets
│   ├── serializers.py         # DRF serializers
│   └── urls.py                # Market endpoints
├── signals/                   # Trading signals
│   ├── models.py              # Signal model
│   ├── views.py               # API views for signals
│   ├── serializers.py         # DRF serializers
│   └── urls.py                # Signal endpoints
├── portfolio/                 # User trades & portfolio
│   ├── models.py              # UserProfile, Trade models
│   ├── views.py               # API views for portfolio
│   ├── serializers.py         # DRF serializers
│   └── urls.py                # Portfolio endpoints
├── backtesting/               # Strategy testing
│   ├── models.py              # Backtest models
│   ├── views.py               # Backtesting views
│   └── engine.py              # Backtesting engine
├── services/                  # External API clients
│   ├── bayse_client.py        # Bayse API integration
│   └── gemini_client.py       # Google Gemini AI integration
├── utils/                     # Utility functions
│   ├── kelly_criterion.py     # Kelly bet sizing
│   ├── expected_value.py      # EV calculations
│   └── performance_metrics.py # Sharpe ratio, drawdown, etc.
├── config/                    # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BAYSE_API_KEY` | API key for Bayse prediction markets | Yes |
| `GEMINI_API_KEY` | Google Gemini API key for AI analysis | Yes |
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | Enable debug mode (True/False) | No (default: False) |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | No |
| `DATABASE_URL` | PostgreSQL connection string (optional) | No |

### Risk Tolerance Levels

Configure in user profile or as default settings:

- **Conservative**: 25% of Kelly criterion
  - Lower risk, smaller position sizes
  - Minimum edge: 20%

- **Balanced**: 50% of Kelly criterion
  - Moderate risk and returns
  - Minimum edge: 15%

- **Aggressive**: 100% of Kelly criterion
  - Higher risk, larger positions
  - Minimum edge: 10%

### Minimum Edge Threshold

Signals require a minimum edge to be generated. Default is **15%** (configurable in `agents/signal_generator.py`):

```python
MIN_EDGE_THRESHOLD = 0.15  # 15% minimum edge
```

---

## Admin Panel

Access the Django admin panel at: `http://127.0.0.1:8000/admin/`

### Available Admin Views

1. **Markets**
   - View all markets
   - See price history charts
   - Monitor market status

2. **Signals**
   - Active and expired signals
   - Signal performance tracking
   - Edge and Kelly calculations

3. **AI Analyses**
   - Quant analysis results
   - AI probability estimates
   - Confidence levels

4. **User Trades**
   - Trade history
   - P&L tracking
   - Position management

5. **Portfolio Profiles**
   - User settings
   - Risk tolerance
   - Performance metrics

---

## Common Commands

### Run Agents Individually

```bash
# Open Django shell
python manage.py shell
```

```python
# Scan markets from Bayse
from agents.market_scanner import scan_markets
scan_markets()

# Analyze a specific market
from agents.quant_analyzer import analyze_market
analyze_market(market_id=1)

# Get AI probability estimate
from agents.ai_probability import get_ai_estimate
get_ai_estimate(market_id=1)

# Generate trading signals
from agents.signal_generator import generate_signal
generate_signal(market_id=1)

# Deactivate expired signals
from agents.signal_generator import deactivate_expired_signals
deactivate_expired_signals()
```

### Database Commands

```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Reset database (careful!)
python manage.py flush

# Export data
python manage.py dumpdata markets.Market > markets_backup.json

# Import data
python manage.py loaddata markets_backup.json
```

### Testing Commands

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test markets
python manage.py test signals
python manage.py test portfolio

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Maintenance Commands

```bash
# Clear expired signals (recommended: run daily)
python manage.py shell -c "from agents.signal_generator import deactivate_expired_signals; deactivate_expired_signals()"

# Update market prices from Bayse
python manage.py shell -c "from agents.market_scanner import update_market_prices; update_market_prices()"

# Generate performance report
python manage.py shell -c "from portfolio.analytics import generate_report; generate_report()"
```

---

## Requirements

- **Python**: 3.9 or higher
- **Django**: 4.2 or higher
- **Django REST Framework**: 3.14+
- **PostgreSQL**: 12+ (optional, SQLite for development)
- **Bayse API**: Active API key required
- **Google Gemini API**: Active API key required

### Key Dependencies

```
Django==4.2
djangorestframework==3.14.0
python-dotenv==1.0.0
requests==2.31.0
google-generativeai==0.3.0
numpy==1.24.0
pandas==2.0.0
psycopg2-binary==2.9.9  # For PostgreSQL
```

---

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set strong `SECRET_KEY`
- [ ] Enable HTTPS
- [ ] Configure CORS settings
- [ ] Set up proper logging
- [ ] Configure rate limiting
- [ ] Set up monitoring (Sentry, etc.)
- [ ] Use environment-specific settings

### Example Production Settings

```python
# In settings.py
DEBUG = False
ALLOWED_HOSTS = ['api.edgeiq.com', 'www.edgeiq.com']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', 5432),
    }
}

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'rest_framework'`
```bash
pip install djangorestframework
```

**Issue**: `ImproperlyConfigured: Set the BAYSE_API_KEY environment variable`
```bash
# Make sure .env file is created and loaded
cp .env.example .env
# Edit .env with your actual API keys
```

**Issue**: Database migration errors
```bash
# Delete migrations and start fresh
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
python manage.py makemigrations
python manage.py migrate
```

**Issue**: API returns 404
```bash
# Verify the URL is correct
# Check that the app is registered in INSTALLED_APPS
# Verify URLs are included in main urls.py
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License.

---

## Support

For issues and questions:
- Open an issue on GitHub
- Contact: support@edgeiq.com

---

## Disclaimer

This software is for educational purposes only. Trading prediction markets involves risk. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.