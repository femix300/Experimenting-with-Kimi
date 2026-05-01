"""
Auth API endpoints for Firebase token exchange.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt

from utils.firebase_client import fs, Collection


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def firebase_login(request):
    """
    Exchange a Firebase ID token for a Django session or JWT.
    
    POST body:
        {"firebase_token": "<id-token-from-firebase-sdk>"}
    
    Returns:
        {"success": true, "user": {"id": ..., "email": ..., "name": ...}}
    """
    firebase_token = request.data.get("firebase_token")
    
    if not firebase_token:
        return Response(
            {"error": "firebase_token is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, firebase_token=firebase_token)
    
    if not user:
        return Response(
            {"error": "Invalid or expired Firebase token"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Django session login
    login(request, user)

    # Sync user profile to Firestore
    profile_data = {
        "firebase_uid": user.username,
        "email": user.email,
        "display_name": user.first_name,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }
    fs.set(Collection.USER_PROFILES, user.username, profile_data, merge=True)

    return Response({
        "success": True,
        "user": {
            "id": user.pk,
            "username": user.username,
            "email": user.email,
            "display_name": user.first_name,
        }
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def firebase_logout(request):
    """Logout the current Django session."""
    logout(request)
    return Response({"success": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """Return current user profile from Firestore."""
    profile = fs.get(Collection.USER_PROFILES, request.user.username)
    return Response({
        "id": request.user.pk,
        "username": request.user.username,
        "email": request.user.email,
        "display_name": request.user.first_name,
        "firestore_profile": profile,
    })
