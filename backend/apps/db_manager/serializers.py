from rest_framework import serializers
from .models import ExternalDatabase, DatabasePermission, GoogleSheetsSync


class ExternalDatabaseSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.username", read_only=True)
    username = serializers.SerializerMethodField()
    password = serializers.SerializerMethodField()

    class Meta:
        model = ExternalDatabase
        fields = [
            "id", "name", "host", "port", "database", "username", "password",
            "is_active", "owner", "owner_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def get_username(self, obj):
        return obj.username

    def get_password(self, obj):
        return "***"



class ExternalDatabaseCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=255, write_only=True)
    password = serializers.CharField(max_length=512, write_only=True)

    class Meta:
        model = ExternalDatabase
        fields = [
            "id", "name", "host", "port", "database", "username", "password", "is_active",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        username = validated_data.pop("username")
        password = validated_data.pop("password")
        db = ExternalDatabase(**validated_data)
        db.username = username
        db.password = password
        db.save()
        return db

    def update(self, instance, validated_data):
        username = validated_data.pop("username", None)
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if username is not None:
            instance.username = username
        if password is not None:
            instance.password = password
        instance.save()
        return instance


class DatabasePermissionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = DatabasePermission
        fields = [
            "id", "user", "username", "database_source", "table_name",
            "can_edit", "can_schema", "can_import", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class GoogleSheetsSyncSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = GoogleSheetsSync
        fields = [
            "id", "name", "spreadsheet_id", "sheet_name", "database_source",
            "table_name", "sync_mode", "key_column", "schedule", "is_active",
            "last_sync_at", "last_sync_status", "last_error",
            "owner", "owner_name", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "owner", "last_sync_at", "last_sync_status", "last_error",
            "created_at", "updated_at",
        ]


class GoogleSheetsSyncCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleSheetsSync
        fields = [
            "id", "name", "spreadsheet_id", "sheet_name", "database_source",
            "table_name", "sync_mode", "key_column", "schedule", "is_active",
            "credentials_json",
        ]
        read_only_fields = ["id"]
