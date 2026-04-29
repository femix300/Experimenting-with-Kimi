"""
Bayse API Client
Handles all interactions with the Bayse prediction market API
"""
import requests
from decimal import Decimal
from decouple import config
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class BayseAPIError(Exception):
    """Custom exception for Bayse API errors"""
    pass


class BayseClient:
    """
    Client for interacting with Bayse API
    Base URL: https://relay.bayse.markets
    """
    
    def __init__(self):
        self.base_url = config('BAYSE_API_BASE_URL', default='https://relay.bayse.markets')
        self.public_key = config('BAYSE_PUBLIC_KEY', default='')
        self.secret_key = config('BAYSE_SECRET_KEY', default='')
        self.timeout = 15  # seconds
        
    def _get_headers(self):
        """Generate headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        if self.public_key:
            headers['X-Public-Key'] = self.public_key
            
        return headers
    
    def _make_request(self, method, endpoint, params=None, data=None):
        """
        Make HTTP request to Bayse API with error handling
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            logger.info(f"Bayse API Request: {method} {url}")
            if params:
                logger.info(f"  Params: {params}")
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=self.timeout
            )
            
            logger.info(f"Bayse API Response: {response.status_code}")
            
            if response.status_code >= 400:
                logger.error(f"Bayse API Error: {response.status_code} - {response.text}")
                raise BayseAPIError(f"API returned {response.status_code}: {response.text}")
            
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"Bayse API Timeout for {endpoint}")
            raise BayseAPIError(f"Request to {endpoint} timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"Bayse API Request Error: {str(e)}")
            raise BayseAPIError(f"Request failed: {str(e)}")
    
    def _get_cached(self, cache_key, fetch_function, timeout=60):
        """Get data from cache or fetch and cache it"""
        data = cache.get(cache_key)
        
        if data is None:
            data = fetch_function()
            if data is not None:
                cache.set(cache_key, data, timeout)
                logger.info(f"Cached data for key: {cache_key}")
        else:
            logger.info(f"Retrieved from cache: {cache_key}")
            
        return data
    
    # ==================== MARKET DATA ENDPOINTS ====================
    
    def get_all_events(self, status='open', category=None, page=1, size=50):
        """
        Fetch all prediction market events
        """
        params = {
            'page': page,
            'size': min(size, 100),
        }
        
        if status:
            params['status'] = status
        if category:
            params['category'] = category
        
        cache_key = f"bayse_events_{status}_{category}_{page}_{size}"
        
        return self._get_cached(
            cache_key,
            lambda: self._make_request('GET', '/v1/pm/events', params=params),
            timeout=60
        )
    
    def get_event_detail(self, event_id):
        """Get detailed information about a specific event"""
        cache_key = f"bayse_event_{event_id}"
        
        return self._get_cached(
            cache_key,
            lambda: self._make_request('GET', f'/v1/pm/events/{event_id}'),
            timeout=60
        )
    
    def get_price_history(self, event_id, outcome='YES', time_period='1W', market_id=None):
        """
        Get historical price data for an event
        Docs: GET /v1/pm/events/{eventId}/price-history?outcome=YES&timePeriod=1W
        
        Args:
            event_id: UUID of the event
            outcome: 'YES' or 'NO' (default: 'YES')
            time_period: '12H', '24H', '1W', '1M', '1Y' (default: '1W')
            market_id: Optional market ID to filter results
        """
        if not event_id:
            logger.error("get_price_history requires event_id")
            return []
        
        params = {
            'outcome': outcome,
            'timePeriod': time_period
        }
        
        # Add marketId[] filter if provided
        if market_id:
            params['marketId[]'] = market_id
        
        cache_key = f"bayse_price_history_{event_id}_{outcome}_{time_period}_{market_id}"
        
        try:
            result = self._get_cached(
                cache_key,
                lambda: self._make_request('GET', f'/v1/pm/events/{event_id}/price-history', params=params),
                timeout=60
            )
            
            # Check if result is a string (error message)
            if isinstance(result, str):
                logger.warning(f"Price history returned string: {result[:100]}")
                return []
            
            # Check if result is a dict with market data
            if result and isinstance(result, dict):
                # Check if it's an error response
                if 'error' in result or 'message' in result:
                    logger.warning(f"Price history API error: {result.get('message', result.get('error', 'Unknown'))}")
                    return []
                
                # Handle Bayse's actual response format with 'markets' array
                if 'markets' in result:
                    all_prices = []
                    for market in result.get('markets', []):
                        market_id_from_response = market.get('marketId')
                        price_history = market.get('priceHistory', [])
                        
                        # If filtering by market_id, only include that market
                        if market_id and market_id_from_response != market_id:
                            continue
                        
                        for price_point in price_history:
                            if isinstance(price_point, dict):
                                # Convert Bayse format (p, e) to standard format
                                all_prices.append({
                                    'price': price_point.get('p', 0),
                                    'timestamp': price_point.get('e', None),
                                    'marketId': market_id_from_response,
                                })
                        
                        # If we found our specific market, we can break
                        if market_id and market_id_from_response == market_id:
                            break
                    
                    logger.info(f"Found {len(all_prices)} price history points for event {event_id}")
                    return all_prices
                
                # OLD: Fallback for the old format (if Bayse ever reverts)
                for mkt_id, prices in result.items():
                    if mkt_id not in ['eventId', 'eventTitle', 'markets'] and isinstance(prices, list):
                        all_prices = []
                        for price_point in prices:
                            if isinstance(price_point, dict):
                                price_point['marketId'] = mkt_id
                                all_prices.append(price_point)
                        return all_prices
                
                return []
            
            return []
            
        except BayseAPIError as e:
            logger.warning(f"Price history not available for event {event_id}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in price history: {str(e)}")
            return []
    
    def get_ticker(self, market_id, outcome='YES'):
        """
        Get current ticker data for a market outcome
        Docs: GET /v1/pm/markets/{marketId}/ticker?outcome=YES
        
        Args:
            market_id: UUID of the market
            outcome: 'YES' or 'NO' (default: 'YES')
        """
        if not market_id:
            logger.error("get_ticker requires market_id")
            return {}
        
        params = {
            'outcome': outcome  # REQUIRED by Bayse API
        }
        
        cache_key = f"bayse_ticker_{market_id}_{outcome}"
        
        try:
            return self._get_cached(
                cache_key,
                lambda: self._make_request('GET', f'/v1/pm/markets/{market_id}/ticker', params=params),
                timeout=30
            )
        except BayseAPIError as e:
            logger.warning(f"Ticker not available for market {market_id}: {str(e)}")
            return {}
    
    def get_order_book(self, outcome_id, depth=10, currency='USD'):
        """
        Get order book for a specific outcome
        Docs: GET /v1/pm/books?outcomeId[]={outcomeId}&depth=10&currency=USD
        
        Args:
            outcome_id: UUID of the outcome (required)
            depth: Number of price levels (default: 10)
            currency: 'USD' or 'NGN' (default: 'USD')
        """
        if not outcome_id:
            logger.error("get_order_book requires outcome_id")
            return {}
        
        params = {
            'outcomeId[]': outcome_id,  # REQUIRED by Bayse API
            'depth': depth,
            'currency': currency
        }
        
        cache_key = f"bayse_orderbook_{outcome_id}_{depth}_{currency}"
        
        try:
            result = self._get_cached(
                cache_key,
                lambda: self._make_request('GET', '/v1/pm/books', params=params),
                timeout=30
            )
            
            # Bayse returns an array of order books
            if result and isinstance(result, list) and len(result) > 0:
                return result[0]  # Return first order book
            return {}
            
        except BayseAPIError as e:
            logger.warning(f"Order book not available for outcome {outcome_id}: {str(e)}")
            return {}
    
    def get_outcome_id(self, event_id, outcome_label='YES'):
        """
        Extract outcome ID from an event
        Supports both 'outcomes' array and 'outcome1Id/outcome2Id' formats
        """
        try:
            event_detail = self.get_event_detail(event_id)
            markets = event_detail.get('markets', [])
            
            for market in markets:
                # NEW: Check for outcome1Id/outcome1Label format (from your Postman response)
                outcome1_label = market.get('outcome1Label', '')
                outcome2_label = market.get('outcome2Label', '')
                
                if outcome_label.upper() == 'YES' and outcome1_label.upper() in ['YES', 'YES', 'Y']:
                    outcome_id = market.get('outcome1Id')
                    if outcome_id:
                        logger.info(f"Found outcome_id {outcome_id} from outcome1Id")
                        return outcome_id
                elif outcome_label.upper() == 'NO' and outcome2_label.upper() in ['NO', 'NO', 'N']:
                    outcome_id = market.get('outcome2Id')
                    if outcome_id:
                        logger.info(f"Found outcome_id {outcome_id} from outcome2Id")
                        return outcome_id
                
                # OLD: Check for outcomes array format
                outcomes = market.get('outcomes', [])
                for outcome in outcomes:
                    label = outcome.get('label') or outcome.get('name')
                    if label and outcome_label.upper() in label.upper():
                        outcome_id = outcome.get('id')
                        if outcome_id:
                            logger.info(f"Found outcome_id {outcome_id} from outcomes array")
                            return outcome_id
            
            logger.warning(f"No outcome_id found for event {event_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get outcome ID: {str(e)}")
            return None
    
    def get_trades(self, market_id=None, event_id=None, limit=50):
        """
        Get recent trades
        
        Endpoint: /v1/pm/trades?marketId={marketId} or ?eventId={eventId}
        """
        params = {'limit': min(limit, 100)}
        
        if market_id:
            params['marketId'] = market_id
        elif event_id:
            params['eventId'] = event_id
        
        cache_key = f"bayse_trades_{market_id or event_id}_{limit}"
        
        try:
            return self._get_cached(
                cache_key,
                lambda: self._make_request('GET', '/v1/pm/trades', params=params),
                timeout=30
            )
        except BayseAPIError as e:
            logger.warning(f"Trades not available: {str(e)}")
            return []
    
    def calculate_implied_probability(self, price):
        """Convert price to implied probability percentage"""
        if isinstance(price, str):
            price = Decimal(price)
        return float(price * 100)


# Global instance
bayse_client = BayseClient()