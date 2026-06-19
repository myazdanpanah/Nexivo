from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import authenticate, get_user_model
from .authentication import JWTAuthentication
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """Authenticate user and return JWT token."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = authenticate(
        username=serializer.validated_data["username"],
        password=serializer.validated_data["password"],
    )

    if user is None:
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token = JWTAuthentication.generate_token(user)

    return Response({
        "token": token,
        "user": UserSerializer(user).data,
    })


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register_view(request):
    """Register a new user."""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token = JWTAuthentication.generate_token(user)

    return Response({
        "token": token,
        "user": UserSerializer(user).data,
    }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def profile_view(request):
    """Get current user profile."""
    return Response(UserSerializer(request.user).data)


@api_view(["PUT"])
def profile_update_view(request):
    """Update current user profile."""
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["GET"])
def users_list_view(request):
    """List all users (admin/CEO only)."""
    if request.user.role not in ("admin", "ceo") and not request.user.is_staff:
        return Response(
            {"error": "Permission denied"},
            status=status.HTTP_403_FORBIDDEN,
        )

    users = User.objects.all().order_by("-date_joined")
    return Response(UserSerializer(users, many=True).data)
