"""User Authentication Views — Firestore-only."""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from utils.firebase_client import fs, Collection
import logging
import uuid

logger = logging.getLogger(__name__)


class UserViewSet(ViewSet):
    """User auth and profile endpoints — Firestore backed."""

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """POST /api/users/register/ — create user in Firestore."""
        username = request.data.get('username', '').strip()
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')

        if not username or not password:
            return Response({
                'success': False,
                'error': 'Username and password required'
            }, status=400)

        user_id = str(uuid.uuid4())
        user_doc = {
            "id": user_id,
            "username": username,
            "email": email,
            "bankroll": float(request.data.get('bankroll', 10000)),
            "risk_tolerance": request.data.get('risk_tolerance', 'medium'),
            "created_at": str(__import__('django').utils.timezone.now()),
        }
        fs.set(Collection.USER_PROFILES, user_id, user_doc)

        return Response({
            'success': True,
            'user': user_doc,
            'token': user_id,  # Simplified — use Firebase Auth tokens in production
            'message': 'User created',
        }, status=201)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """POST /api/users/login/ — lookup user in Firestore."""
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')  # Not validated yet (TODO: Firebase Auth)

        # Simple lookup by username in Firestore
        users = fs.query(
            Collection.USER_PROFILES,
            filters=[("username", "==", username)],
            limit=1,
        )
        if users:
            user = users[0]
            return Response({
                'success': True,
                'user': user,
                'token': user.get('id'),
                'message': 'Login successful',
            })

        return Response({
            'success': False,
            'error': 'Invalid credentials'
        }, status=401)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """POST /api/users/logout/"""
        return Response({'success': True, 'message': 'Logged out'})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """GET /api/users/profile/ — from Firestore."""
        user_id = str(request.user.id) if request.user.is_authenticated else None
        if not user_id:
            return Response({'success': False, 'error': 'Not authenticated'}, status=401)

        profile = fs.get(Collection.USER_PROFILES, user_id)
        if profile:
            return Response({'success': True, 'profile': profile})

        return Response({'success': False, 'error': 'Profile not found'}, status=404)

    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """PATCH /api/users/update_profile/ — update Firestore."""
        user_id = str(request.user.id) if request.user.is_authenticated else None
        if not user_id:
            return Response({'success': False, 'error': 'Not authenticated'}, status=401)

        updates = {}
        if 'risk_tolerance' in request.data:
            updates['risk_tolerance'] = request.data['risk_tolerance']
        if 'bankroll' in request.data:
            updates['bankroll'] = float(request.data['bankroll'])

        if updates:
            fs.update(Collection.USER_PROFILES, user_id, updates)

        profile = fs.get(Collection.USER_PROFILES, user_id)
        return Response({'success': True, 'profile': profile})
