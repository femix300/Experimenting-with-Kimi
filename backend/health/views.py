"""Health check endpoint for EdgeIQ."""
import time
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from services.bayse_client import BayseClient
from services.gemini_client import GeminiClient
from utils.firebase_client import FirestoreClient

@require_http_methods(["GET"])
def health_check(request):
    start = time.time()
    services = {}
    overall = "healthy"

    # Bayse — hit home /
    try:
        BayseClient()._make_request('GET', '/')
        services["bayse_api"] = {"status": "healthy"}
    except Exception as e:
        services["bayse_api"] = {"status": "unhealthy", "error": str(e)}
        overall = "degraded"

    # Gemini — quick generate
    try:
        c = GeminiClient()
        if c.client:
            c.client.models.generate_content(
                model='gemini-2.5-flash',
                contents='ok',
                config={'max_output_tokens': 3}
            )
        services["gemini_api"] = {"status": "healthy" if c.client else "unhealthy"}
    except Exception as e:
        services["gemini_api"] = {"status": "unhealthy", "error": str(e)}
        overall = "degraded"

    # Firestore
    try:
        fb = FirestoreClient()
        if fb.db:
            fb.db.collection("health_checks").document("ping").set({"ts": time.time()})
        services["firestore"] = {"status": "healthy" if fb.db else "unhealthy"}
    except Exception as e:
        services["firestore"] = {"status": "unhealthy", "error": str(e)}
        overall = "degraded"

    return JsonResponse({
        "status": overall,
        "response_time_ms": round((time.time() - start) * 1000, 1),
        "services": services,
    })
