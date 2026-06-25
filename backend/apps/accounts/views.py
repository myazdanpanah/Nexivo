from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import authenticate, get_user_model
from .authentication import JWTAuthentication
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


def _is_admin_or_ceo(user):
    return user.role in ("admin", "ceo") or user.is_staff


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


# ---- User Management (admin/CEO only) ----

@api_view(["GET", "POST"])
def users_list_create_view(request):
    """List all users or create a new user (admin/CEO only)."""
    if not _is_admin_or_ceo(request.user):
        return Response(
            {"error": "Permission denied"},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == "GET":
        users = User.objects.all().order_by("-date_joined")
        return Response(UserSerializer(users, many=True).data)

    elif request.method == "POST":
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


@api_view(["GET", "PUT", "DELETE"])
def user_detail_view(request, pk):
    """Retrieve, update, or delete a user (admin/CEO only)."""
    if not _is_admin_or_ceo(request.user):
        return Response(
            {"error": "Permission denied"},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(UserSerializer(user).data)

    elif request.method == "PUT":
        # Enforce role hierarchy: can only assign roles at or below your level
        ROLE_HIERARCHY = {"sales": 1, "finance": 2, "admin": 3, "ceo": 4}
        requested_role = request.data.get("role")
        if requested_role and requested_role in ROLE_HIERARCHY:
            caller_level = ROLE_HIERARCHY.get(request.user.role, 0)
            target_level = ROLE_HIERARCHY.get(requested_role, 0)
            if target_level > caller_level and not request.user.is_staff:
                return Response(
                    {"error": "Cannot assign a role higher than your own"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        allowed_fields = ["username", "email", "first_name", "last_name", "role", "department"]
        for field in allowed_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()
        return Response(UserSerializer(user).data)

    elif request.method == "DELETE":
        # Prevent self-deletion
        if user.id == request.user.id:
            return Response(
                {"error": "Cannot delete yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
