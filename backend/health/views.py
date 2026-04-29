"""
Health check endpoint for EdgeIQ.
Tests all external dependencies: Bayse API, Gemini API, Firestore.
"""
import time
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from services.bayse_client import BayseClient
from services.gemini_client import GeminiClient
from utils.firebase_client import FirebaseClient
import os


@require_http_methods(["GET"])
def health_check(request):
    """Check health of all external services."""
    start_time = time.time()
    services = {}
    overall_status = "healthy"

    # Check Bayse API
    try:
        client = BayseClient()
        # Lightweight check - just get events with small limit
        response = client.get("/v1/pm/events", {"limit": 1, "page": 1})
        services["bayse_api"] = {
            "status": "healthy",
            "response_time_ms": round((time.time() - start_time) * 1000, 1),
        }
    except Exception as e:
        services["bayse_api"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        overall_status = "degraded"

    # Check Gemini API
    try:
        gemini_client = GeminiClient()
        # Use the cheapest model for health check
        response = gemini_client.models[0].generate_content("Say 'ok'", generation_config={"max_output_tokens": 5})
        services["gemini_api"] = {
            "status": "healthy",
            "model": gemini_client.current_model_name or gemini_client.models[0].name,
        }
    except Exception as e:
        services["gemini_api"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        overall_status = "degraded"

    # Check Firestore
    try:
        fb_client = FirebaseClient()
        # Try to read a document
        test_doc = fb_client.db.collection("health_checks").document("ping")
        test_doc.set({"timestamp": time.time(), "status": "ok"})
        services["firestore"] = {
            "status": "healthy",
        }
    except Exception as e:
        services["firestore"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        overall_status = "degraded"

    response_time = round((time.time() - start_time) * 1000, 1)

    return JsonResponse({
        "status": overall_status,
        "response_time_ms": response_time,
        "services": services,
        "version": "1.0.0",
        "environment": os.environ.get("DJANGO_ENV", "development"),
    })
