"""LLM gateway serializers."""

from rest_framework import serializers
from .models import LLMProvider, LLMUsageLog, LLMChatSession, LLMChatMessage


class LLMProviderSerializer(serializers.ModelSerializer):
    has_key = serializers.BooleanField(read_only=True)

    class Meta:
        model = LLMProvider
        fields = [
            "id", "provider_type", "name", "model_name",
            "api_base_url", "has_key",
            "temperature", "max_tokens",
            "is_active", "is_default",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LLMProviderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMProvider
        fields = [
            "id", "provider_type", "name", "model_name",
            "api_base_url", "api_key",
            "temperature", "max_tokens",
            "is_active", "is_default",
        ]
        read_only_fields = ["id"]


class LLMUsageLogSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.name", read_only=True, default=None)
    username = serializers.CharField(source="user.username", read_only=True, default=None)

    class Meta:
        model = LLMUsageLog
        fields = [
            "id", "provider", "provider_name", "user", "username",
            "feature", "prompt_tokens", "completion_tokens", "total_tokens",
            "duration_ms", "created_at",
        ]


class LLMChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMChatMessage
        fields = ["id", "role", "content", "metadata", "created_at"]


class LLMChatSessionSerializer(serializers.ModelSerializer):
    messages = LLMChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = LLMChatSession
        fields = ["id", "title", "feature", "messages", "message_count", "created_at", "updated_at"]

    def get_message_count(self, obj):
        return obj.messages.count()


class LLMChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    session_id = serializers.IntegerField(required=False, allow_null=True)
    feature = serializers.CharField(default="chat")


class LLMTestRequestSerializer(serializers.Serializer):
    provider_id = serializers.IntegerField()
    message = serializers.CharField(default="Hello, are you working?")
