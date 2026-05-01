"""
Firebase Authentication Backend for Django
===========================================
Verifies Firebase ID tokens and maps them to Django users.
Replaces SQLite-based auth for Cloud Run deployment.
"""
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import FirebaseError

logger = logging.getLogger(__name__)

User = get_user_model()


class FirebaseAuthBackend(BaseBackend):
    """
    Authenticate against Firebase Auth.
    
    The frontend sends a Firebase ID token in the Authorization header.
    Django verifies the token and creates/retrieves a local User record.
    """

    def authenticate(self, request, firebase_token=None, **kwargs):
        if not firebase_token:
            return None

        try:
            # Verify the ID token with Firebase
            decoded_token = firebase_auth.verify_id_token(
                firebase_token,
                check_revoked=True
            )
        except (FirebaseError, ValueError) as e:
            logger.warning(f"Firebase token verification failed: {e}")
            return None

        uid = decoded_token.get("uid")
        if not uid:
            return None

        email = decoded_token.get("email", "")
        display_name = decoded_token.get("name", "")

        # Get or create local user record
        try:
            user = User.objects.get(username=uid)
            # Update email/name if changed
            if user.email != email or user.first_name != display_name:
                user.email = email
                user.first_name = display_name
                user.save(update_fields=["email", "first_name"])
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=uid,
                email=email,
                first_name=display_name,
                # Random unusable password — auth is handled by Firebase
                password=None,
            )

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class FirebaseTokenMiddleware:
    """
    Middleware that extracts the Firebase ID token from the Authorization
    header and authenticates the user via FirebaseAuthBackend.
    
    Expected header format:
        Authorization: Bearer <firebase-id-token>
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get("Authorization", "")
        
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            from django.contrib.auth import authenticate
            user = authenticate(request, firebase_token=token)
            if user:
                request.user = user

        response = self.get_response(request)
        return response
