from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Company, Division, Team, CustomRole

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True, default=None)
    division_name = serializers.CharField(source='division.name', read_only=True, default=None)
    team_name = serializers.CharField(source='team.name', read_only=True, default=None)
    reports_to_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "role", "department", "is_staff",
            "company", "company_name",
            "division", "division_name",
            "team", "team_name",
            "reports_to", "reports_to_name",
        ]
        read_only_fields = ["id"]

    def get_reports_to_name(self, obj):
        if obj.reports_to:
            return f"{obj.reports_to.first_name} {obj.reports_to.last_name}".strip() or obj.reports_to.username
        return None


class CompanySerializer(serializers.ModelSerializer):
    division_count = serializers.SerializerMethodField()
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ["id", "name", "description", "is_active", "division_count", "employee_count", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_division_count(self, obj):
        return obj.divisions.count()

    def get_employee_count(self, obj):
        return obj.employees.count()


class DivisionSerializer(serializers.ModelSerializer):
    manager_name = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Division
        fields = [
            "id", "company", "name", "description",
            "manager", "manager_name", "parent",
            "is_active", "team_count", "employee_count", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_manager_name(self, obj):
        if obj.manager:
            return f"{obj.manager.first_name} {obj.manager.last_name}".strip() or obj.manager.username
        return None

    def get_team_count(self, obj):
        return obj.teams.count()

    def get_employee_count(self, obj):
        return obj.employees.count()


class TeamSerializer(serializers.ModelSerializer):
    manager_name = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    division_name = serializers.CharField(source='division.name', read_only=True)
    company_name = serializers.CharField(source='division.company.name', read_only=True)

    class Meta:
        model = Team
        fields = [
            "id", "division", "name", "description",
            "manager", "manager_name",
            "is_active", "member_count",
            "division_name", "company_name", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_manager_name(self, obj):
        if obj.manager:
            return f"{obj.manager.first_name} {obj.manager.last_name}".strip() or obj.manager.username
        return None

    def get_member_count(self, obj):
        return obj.members.count()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name", "last_name", "role", "department", "company", "division", "team", "reports_to"]

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class CustomRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomRole
        fields = ['id', 'value', 'label', 'color', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
