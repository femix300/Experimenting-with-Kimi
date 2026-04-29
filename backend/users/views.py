"""
User Authentication Views
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .serializers import UserSerializer, UserProfileSerializer, RegisterSerializer, LoginSerializer
from .models import UserProfile, sync_profile_to_firestore
from utils.firebase_client import fs, Collection
import logging

logger = logging.getLogger(__name__)


class UserViewSet(ViewSet):
    """
    User authentication and profile endpoints
    """
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Register a new user
        POST /api/users/register/
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            
            # Sync to Firestore
            sync_profile_to_firestore(user)
            
            return Response({
                'success': True,
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'User created successfully'
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Login user
        POST /api/users/login/
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'success': True,
                    'user': UserSerializer(user).data,
                    'token': token.key,
                    'message': 'Login successful'
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Logout user (delete token)
        POST /api/users/logout/
        """
        try:
            request.user.auth_token.delete()
            return Response({
                'success': True,
                'message': 'Logged out successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """
        Get current user's profile
        GET /api/users/profile/
        """
        try:
            # Try to get from Firestore first
            firestore_profile = fs.get(Collection.USER_PROFILES, str(request.user.id))
            if firestore_profile:
                return Response({
                    'success': True,
                    'profile': firestore_profile
                })
            
            # Fallback to SQLite
            profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(profile)
            return Response({
                'success': True,
                'profile': serializer.data
            })
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """
        Update user profile
        PATCH /api/users/update_profile/
        """
        try:
            profile = UserProfile.objects.get(user=request.user)
            
            if 'risk_tolerance' in request.data:
                profile.risk_tolerance = request.data['risk_tolerance']
            if 'bankroll' in request.data:
                profile.bankroll = request.data['bankroll']
            
            profile.save()
            
            # Sync to Firestore
            sync_profile_to_firestore(request.user)
            
            serializer = UserProfileSerializer(profile)
            return Response({
                'success': True,
                'profile': serializer.data
            })
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
