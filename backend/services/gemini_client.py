"""
Google Gemini API Client with Auto-Failover
Two-Step Agent Pipeline for Production-Grade Structured Outputs
"""
from google import genai
from google.genai.types import GenerateContentConfig, GoogleSearch
from pydantic import BaseModel
from decouple import config
import json
import logging
import time

logger = logging.getLogger(__name__)

# Define the exact schema the database requires
class AIAnalysisSchema(BaseModel):
    probability: float
    confidence: float
    reasoning: str
    key_factors: list[str]
    sources_consulted: str

# Available models in order of preference
AVAILABLE_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.5-pro',
    'gemini-2.0-flash',
]
class GeminiClient:
    """Client for Google Gemini AI with automatic model failover"""
    
    def __init__(self):
        self.api_key = config('GEMINI_API_KEY', default='')
        self._failed_models = set()  # Track exhausted models in this session
        
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Gemini client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {str(e)}")
                self.client = None
        else:
            logger.warning("No Gemini API key configured")
            self.client = None
    
    def _get_available_model(self):
        """Get first model that hasn't been exhausted"""
        for model in AVAILABLE_MODELS:
            if model not in self._failed_models:
                return model
        return None
    
    def _mark_model_exhausted(self, model_name):
        """Mark a model as exhausted"""
        self._failed_models.add(model_name)
        logger.warning(f"Model {model_name} exhausted, will try next")
    
    def _generate_with_retry(self, model, contents, config, max_retries=2):
        """Generate content with retry on quota errors, returns (response, model_used)"""
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                return response, model  # Return both response and the model that worked
            except Exception as e:
                error_str = str(e)
                if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                    logger.warning(f"Model {model} quota exhausted (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                    else:
                        return None, model
                else:
                    logger.error(f"Error with model {model}: {error_str}")
                    return None, model
        return None, model
    
    def estimate_probability(self, event_title, event_description, market_context=None):
        """Two-Step Production Pipeline with auto-failover"""
        if not self.client:
            logger.error("Gemini client not initialized - no API key")
            return self._default_response()
        
        # Get available model
        model_to_try = self._get_available_model()
        if not model_to_try:
            logger.error("All Gemini models exhausted")
            return self._default_response("All AI models currently unavailable")
        
        actual_model_used = model_to_try  # Will be updated if failover happens
        
        try:
            logger.info(f"Phase 1: Researching '{event_title[:50]}...' using {model_to_try}")
            
            # ==========================================
            # STEP 1: THE RESEARCHER (Uses Google Search)
            # ==========================================
            research_prompt = self._build_research_prompt(event_title, event_description, market_context)
            
            research_config = GenerateContentConfig(
                temperature=0.3,
                tools=[GoogleSearch()],
            )
            
            research_response, research_model = self._generate_with_retry(
                model=model_to_try,
                contents=research_prompt,
                config=research_config,
            )
            
            if research_response is None:
                self._mark_model_exhausted(model_to_try)
                return self.estimate_probability(event_title, event_description, market_context)
            
            actual_model_used = research_model  # Update with actual model that worked
            
            logger.info("Phase 2: Formatting output into strict JSON schema")
            
            # ==========================================
            # STEP 2: THE FORMATTER (Uses Strict Schema)
            # ==========================================
            format_prompt = f"""
            Extract the data from the following research report into the required JSON schema.
            Make sure the reasoning is a single continuous paragraph without line breaks.
            
            RESEARCH REPORT:
            {research_response.text}
            """
            
            format_config = GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=AIAnalysisSchema,
            )
            
            final_response, format_model = self._generate_with_retry(
                model=actual_model_used,
                contents=format_prompt,
                config=format_config,
            )
            
            if final_response is None:
                self._mark_model_exhausted(actual_model_used)
                return self.estimate_probability(event_title, event_description, market_context)
            
            actual_model_used = format_model  # Update again (should be same as research_model)
            
            # Parse the guaranteed perfect JSON
            result = self._parse_response(final_response.text)
            
            # 🔥 THIS IS THE KEY - Return the actual model that was used
            result['model_used'] = actual_model_used
            
            logger.info(f"✅ Pipeline Complete: {result['probability']}% (Confidence: {result['confidence']}%) using {actual_model_used}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Gemini Pipeline: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._default_response()

    def _build_research_prompt(self, title, description, context=None):
        """Build prompt for the Research phase"""
        prompt = f"""You are a quantitative analyst. Analyze the following prediction market event:
Title: {title}
Description: {description}

Search the web for the latest news regarding this event.
Write a comprehensive summary including:
1. A final probability percentage (0-100)
2. Your confidence level in this prediction (0-100)
3. A 2-3 sentence reasoning summary
4. 3-5 key factors driving this prediction
5. The main sources or news you found
"""
        if context:
            prompt += f"\nCurrent Market Price: ₦{context.get('current_price', 'N/A')}"
            prompt += f"\nMarket Implied Probability: {context.get('implied_probability', 'N/A')}%"
            
        return prompt

    def _parse_response(self, response_text):
        """Parse the guaranteed perfect JSON from the Formatter phase"""
        try:
            data = json.loads(response_text)
            
            # Get raw probability
            prob_raw = float(data.get('probability', 50.0))
            
            # NORMALIZE: If value is between 0 and 1, assume it's 0-1 scale and convert to 0-100
            if 0 < prob_raw <= 1:
                prob_raw = prob_raw * 100
                logger.info(f"Normalized probability from {data.get('probability')} to {prob_raw}")
            
            # Get raw confidence and normalize similarly
            conf_raw = float(data.get('confidence', 50.0))
            if 0 < conf_raw <= 1:
                conf_raw = conf_raw * 100
                logger.info(f"Normalized confidence from {data.get('confidence')} to {conf_raw}")
            
            return {
                'probability': prob_raw,
                'confidence': conf_raw,
                'reasoning': str(data.get('reasoning', 'Analysis complete')).replace('\n', ' '),
                'key_factors': data.get('key_factors', [])[:5],
                'sources_consulted': str(data.get('sources_consulted', ''))[:200]
            }
        except Exception as e:
            logger.error(f"Critical error parsing JSON: {str(e)}")
            return self._default_response()

    def _default_response(self, custom_message=None):
        """Fallback for critical failures"""
        message = custom_message or 'AI analysis unavailable due to system error.'
        return {
            'probability': 50.0,
            'confidence': 0.0,
            'reasoning': message,
            'key_factors': [],
            'sources_consulted': '',
            'model_used': 'fallback'
        }


# Global instance
gemini_client = GeminiClient()