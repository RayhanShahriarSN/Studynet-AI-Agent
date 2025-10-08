# Authentication views for JWT-based authentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Token Generation Helper
# ============================================================================

def get_tokens_for_user(user):
    """Generate JWT tokens for a user

    Args:
        user: Django User object

    Returns:
        dict with refresh and access tokens

    Raises:
        Exception if user is not active
    """
    if not user.is_active:
        raise Exception("User account is disabled")

    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# ============================================================================
# Authentication Endpoints
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """Register a new user account

    Expected JSON payload:
    {
        "username": "string",
        "email": "string",
        "password": "string",
        "password_confirm": "string",
        "first_name": "string" (optional),
        "last_name": "string" (optional)
    }

    Returns:
        201: User created with tokens
        400: Validation errors
    """
    try:
        # Extract data
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        password_confirm = request.data.get('password2') or request.data.get('password_confirm')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        # Validation
        if not username or not email or not password:
            return Response(
                {"error": "Username, email, and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if password != password_confirm:
            return Response(
                {"error": "Passwords do not match"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if username exists
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if email exists
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "Email already registered"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            return Response(
                {"error": list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Generate tokens
        tokens = get_tokens_for_user(user)

        # Store bearer token in user profile
        from .user_profile import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.bearer_token = tokens['access']
        profile.save()

        logger.info(f"New user registered: {username}")

        return Response({
            "message": "User registered successfully",
            "access": tokens['access'],
            "refresh": tokens['refresh'],
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_admin": user.is_superuser,
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Registration error: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Login user and return JWT tokens

    Expected JSON payload:
    {
        "username": "string",
        "password": "string"
    }

    Returns:
        200: Login successful with tokens
        401: Invalid credentials
        400: Missing fields
    """
    try:
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"error": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate user
        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {"error": "Invalid username or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {"error": "User account is disabled"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate tokens
        tokens = get_tokens_for_user(user)

        # Store/Update bearer token in user profile
        from .user_profile import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.bearer_token = tokens['access']
        profile.save()

        logger.info(f"User logged in: {username}")

        return Response({
            "message": "Login successful",
            "access": tokens['access'],
            "refresh": tokens['refresh'],
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Login error: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def token_refresh_view(request):
    """Refresh access token using refresh token

    Expected JSON payload:
    {
        "refresh": "string"
    }

    Returns:
        200: New access token
        401: Invalid refresh token
    """
    try:
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            return Response({
                "access": access_token
            }, status=status.HTTP_200_OK)

        except (TokenError, InvalidToken) as e:
            return Response(
                {"error": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED
            )

    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def logout_view(request):
    """Logout user by blacklisting refresh token

    Expected JSON payload:
    {
        "refresh": "string"
    }

    Returns:
        200: Logout successful
        400: Missing refresh token
    """
    try:
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            logger.info(f"User logged out: {request.user.username}")

            return Response({
                "message": "Logout successful"
            }, status=status.HTTP_200_OK)

        except (TokenError, InvalidToken):
            return Response(
                {"error": "Invalid refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def user_profile_view(request):
    """Get current user profile

    Requires authentication.

    Returns:
        200: User profile data
    """
    try:
        user = request.user

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "is_admin": user.is_superuser,
            "date_joined": user.date_joined,
            "last_login": user.last_login,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Profile retrieval error: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
def update_profile_view(request):
    """Update current user profile

    Requires authentication.

    Expected JSON payload (all fields optional):
    {
        "email": "string",
        "first_name": "string",
        "last_name": "string"
    }

    Returns:
        200: Profile updated successfully
    """
    try:
        user = request.user

        # Update fields if provided
        if 'email' in request.data:
            email = request.data['email']
            if User.objects.exclude(id=user.id).filter(email=email).exists():
                return Response(
                    {"error": "Email already in use"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.email = email

        if 'first_name' in request.data:
            user.first_name = request.data['first_name']

        if 'last_name' in request.data:
            user.last_name = request.data['last_name']

        user.save()

        logger.info(f"Profile updated: {user.username}")

        return Response({
            "message": "Profile updated successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# User Statistics (Students Only)
# ============================================================================

@api_view(['GET'])
def user_stats_view(request):
    """Get user statistics - students can only view their own stats

    Returns:
        200: User statistics
        403: Permission denied
    """
    try:
        # Students can only view their own stats
        target_user = request.user

        from api.models import QueryAnalytics, ConversationSession, CSVUpload, DocumentUpload
        from django.db.models import Sum, Avg, Count

        # Get analytics
        analytics = QueryAnalytics.objects.filter(user=target_user)

        # Aggregate stats
        stats = analytics.aggregate(
            total_queries=Count('id'),
            total_tokens=Sum('tokens_used'),
            total_cost=Sum('total_cost_usd'),
            avg_response_time=Avg('response_time_ms'),
            avg_confidence=Avg('confidence_score'),
        )

        # Query type breakdown
        query_types = {
            'sql': analytics.filter(query_type='structured_sql').count(),
            'rag': analytics.filter(query_type='semantic_rag').count(),
            'hybrid': analytics.filter(query_type='hybrid').count(),
        }

        # Sessions
        sessions_count = ConversationSession.objects.filter(user=target_user).count()

        # Uploads
        csv_uploads = CSVUpload.objects.filter(user=target_user).count()
        doc_uploads = DocumentUpload.objects.filter(user=target_user).count()

        return Response({
            "user": {
                "id": target_user.id,
                "username": target_user.username,
                "full_name": f"{target_user.first_name} {target_user.last_name}".strip() or target_user.username
            },
            "statistics": {
                "total_queries": stats['total_queries'] or 0,
                "total_tokens": stats['total_tokens'] or 0,
                "total_cost_usd": float(stats['total_cost'] or 0),
                "avg_response_time_ms": round(stats['avg_response_time'] or 0, 2),
                "avg_confidence_score": round(stats['avg_confidence'] or 0, 2),
                "query_types": query_types,
                "sessions_count": sessions_count,
                "csv_uploads": csv_uploads,
                "document_uploads": doc_uploads,
            }
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"User stats error: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# HTML Page Views
# ============================================================================

def login_page_view(request):
    """Render the login page"""
    return render(request, 'login.html')


def register_page_view(request):
    """Render the registration page"""
    return render(request, 'register.html')


# ============================================================================
# Password Management
# ============================================================================

@api_view(['POST'])
def change_password_view(request):
    """Change user password

    Requires authentication.

    Expected JSON payload:
    {
        "old_password": "string",
        "new_password": "string",
        "new_password_confirm": "string"
    }

    Returns:
        200: Password changed successfully
        400: Validation errors
    """
    try:
        user = request.user

        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        new_password_confirm = request.data.get('new_password_confirm')

        if not all([old_password, new_password, new_password_confirm]):
            return Response(
                {"error": "All password fields are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check old password
        if not user.check_password(old_password):
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check password match
        if new_password != new_password_confirm:
            return Response(
                {"error": "New passwords do not match"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate password strength
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {"error": list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(new_password)
        user.save()

        logger.info(f"Password changed: {user.username}")

        return Response({
            "message": "Password changed successfully"
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Password change error: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
