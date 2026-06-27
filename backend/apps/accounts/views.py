from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import authenticate, get_user_model
from django.db import models
from .authentication import JWTAuthentication
from .serializers import (
    LoginSerializer, RegisterSerializer, UserSerializer,
    CompanySerializer, DivisionSerializer, TeamSerializer,
)
from .models import Company, Division, Team

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

        allowed_fields = [
            "username", "email", "first_name", "last_name", "role", "department",
            "company", "division", "team", "reports_to",
        ]
        old_division = user.division_id
        old_team = user.team_id
        for field in allowed_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()

        # Auto-assignment: when a user is added to a division or team,
        # check if that org unit has existing dashboard assignments and
        # replicate them for the new user.
        new_division = user.division_id
        new_team = user.team_id
        if (new_division and new_division != old_division) or (new_team and new_team != old_team):
            from apps.dashboards.models import DashboardAssignment, Dashboard
            existing_assignments = DashboardAssignment.objects.filter(
                is_active=True,
            ).filter(
                models.Q(assigned_to__division_id=new_division) | models.Q(assigned_to__team_id=new_team)
            ).values_list('dashboard_id', 'data_filters', 'visible_pages').distinct()
            assigned_dash_ids = set()
            for dash_id, d_filters, v_pages in existing_assignments:
                if dash_id not in assigned_dash_ids:
                    DashboardAssignment.objects.get_or_create(
                        dashboard_id=dash_id,
                        assigned_to=user,
                        defaults={
                            "assigned_by": request.user,
                            "data_filters": d_filters or [],
                            "visible_pages": v_pages or [],
                            "notes": f"خودکار: اضافه شده به ساختار سازمانی",
                            "is_active": True,
                        },
                    )
                    assigned_dash_ids.add(dash_id)

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


# ---- Organization Management (Company → Division → Team) ----

@api_view(["GET", "POST"])
def company_list_create(request):
    """List all companies or create a new one (admin/CEO only)."""
    if not _is_admin_or_ceo(request.user):
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        companies = Company.objects.all()
        return Response(CompanySerializer(companies, many=True).data)
    elif request.method == "POST":
        serializer = CompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def company_detail(request, pk):
    """Retrieve, update, or delete a company."""
    if not _is_admin_or_ceo(request.user):
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
    try:
        company = Company.objects.get(pk=pk)
    except Company.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(CompanySerializer(company).data)
    elif request.method == "PUT":
        serializer = CompanySerializer(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    elif request.method == "DELETE":
        company.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "POST"])
def division_list_create(request):
    """List divisions (optionally filtered by company) or create a new one."""
    if not _is_admin_or_ceo(request.user):
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        divisions = Division.objects.select_related("company", "manager").all()
        company_id = request.query_params.get("company_id")
        if company_id:
            divisions = divisions.filter(company_id=company_id)
        return Response(DivisionSerializer(divisions, many=True).data)
    elif request.method == "POST":
        serializer = DivisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def division_detail(request, pk):
    """Retrieve, update, or delete a division."""
    if not _is_admin_or_ceo(request.user):
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
    try:
        division = Division.objects.select_related("company", "manager").get(pk=pk)
    except Division.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(DivisionSerializer(division).data)
    elif request.method == "PUT":
        serializer = DivisionSerializer(division, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    elif request.method == "DELETE":
        division.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "POST"])
def team_list_create(request):
    """List teams (optionally filtered by division) or create a new one."""
    if not _is_admin_or_ceo(request.user):
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        teams = Team.objects.select_related("division", "division__company", "manager").all()
        division_id = request.query_params.get("division_id")
        company_id = request.query_params.get("company_id")
        if division_id:
            teams = teams.filter(division_id=division_id)
        elif company_id:
            teams = teams.filter(division__company_id=company_id)
        return Response(TeamSerializer(teams, many=True).data)
    elif request.method == "POST":
        serializer = TeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def team_detail(request, pk):
    """Retrieve, update, or delete a team."""
    if not _is_admin_or_ceo(request.user):
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
    try:
        team = Team.objects.select_related("division", "division__company", "manager").get(pk=pk)
    except Team.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(TeamSerializer(team).data)
    elif request.method == "PUT":
        serializer = TeamSerializer(team, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    elif request.method == "DELETE":
        team.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def org_tree(request):
    """Return the full organization tree: Companies → Divisions → Teams with members (admin/CEO only)."""
    if not _is_admin_or_ceo(request.user):
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    companies = Company.objects.prefetch_related(
        'divisions', 'divisions__teams', 'divisions__manager', 'divisions__teams__manager',
        'employees', 'divisions__employees', 'divisions__teams__members',
    ).all()

    result = []
    for company in companies:
        divs = []
        for div in company.divisions.all():
            teams = []
            for team in div.teams.all():
                members = [
                    {"id": m.id, "username": m.username, "name": f"{m.first_name} {m.last_name}".strip() or m.username, "role": m.role}
                    for m in team.members.all()
                ]
                teams.append({
                    "id": team.id,
                    "name": team.name,
                    "description": team.description,
                    "manager": team.manager.username if team.manager else None,
                    "manager_name": f"{team.manager.first_name} {team.manager.last_name}".strip() if team.manager else None,
                    "member_count": len(members),
                    "members": members,
                })
            div_employees = [
                {"id": e.id, "username": e.username, "name": f"{e.first_name} {e.last_name}".strip() or e.username, "role": e.role}
                for e in div.employees.all() if not e.team
            ]
            divs.append({
                "id": div.id,
                "name": div.name,
                "description": div.description,
                "manager": div.manager.username if div.manager else None,
                "manager_name": f"{div.manager.first_name} {div.manager.last_name}".strip() if div.manager else None,
                "teams": teams,
                "employees": div_employees,
            })
        company_employees = [
            {"id": e.id, "username": e.username, "name": f"{e.first_name} {e.last_name}".strip() or e.username, "role": e.role}
            for e in company.employees.all() if not e.division
        ]
        result.append({
            "id": company.id,
            "name": company.name,
            "description": company.description,
            "divisions": divs,
            "employees": company_employees,
        })

    return Response(result)
