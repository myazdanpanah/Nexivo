"""
LLM Gateway Views — Provider management, chat, and usage tracking.

Security:
- Rate limiting via DRF throttling
- Company-scoped queries
- Chat history capped at 50 messages
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response

from .models import LLMProvider, LLMUsageLog, LLMChatSession, LLMChatMessage
from .serializers import (
    LLMProviderSerializer, LLMProviderCreateSerializer,
    LLMUsageLogSerializer, LLMChatSessionSerializer, LLMChatMessageSerializer,
    LLMChatRequestSerializer, LLMTestRequestSerializer,
)
from .service import chat_completion, get_provider

logger = logging.getLogger(__name__)

# Max messages to keep in context window per session
MAX_CHAT_HISTORY = 50


class LLMChatThrottle(UserRateThrottle):
    """Rate limit LLM chat requests: 10/minute per user."""
    rate = "10/minute"
    scope = "llm_chat"


class LLMTestThrottle(UserRateThrottle):
    """Rate limit LLM test requests: 10/minute per user."""
    rate = "10/minute"
    scope = "llm_test"


# ─── Provider Management ─────────────────────────────────────────

@api_view(["GET", "POST"])
def provider_list(request):
    """List or create LLM providers for the user's company."""
    company = request.user.company
    if not company:
        return Response({"error": "No company assigned"}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "GET":
        providers = LLMProvider.objects.filter(company=company)
        # Mask API keys in response
        data = LLMProviderSerializer(providers, many=True).data
        for item in data:
            if item.get("api_key"):
                item["api_key"] = "••••••••" + item["api_key"][-4:] if len(item["api_key"]) > 4 else "••••"
        return Response(data)

    elif request.method == "POST":
        data = request.data.copy()
        data["company"] = company.id
        serializer = LLMProviderCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        provider = serializer.save(company=company)
        return Response(LLMProviderSerializer(provider).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def provider_detail(request, pk):
    """Retrieve, update, or delete an LLM provider."""
    company = request.user.company
    try:
        provider = LLMProvider.objects.get(pk=pk, company=company)
    except LLMProvider.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        data = LLMProviderSerializer(provider).data
        if data.get("api_key"):
            data["api_key"] = "••••••••" + data["api_key"][-4:] if len(data["api_key"]) > 4 else "••••"
        return Response(data)

    elif request.method == "PUT":
        serializer = LLMProviderCreateSerializer(provider, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        provider = serializer.save()
        return Response(LLMProviderSerializer(provider).data)

    elif request.method == "DELETE":
        provider.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def provider_set_active(request, pk):
    """Set a provider as the active one for the company."""
    company = request.user.company
    try:
        provider = LLMProvider.objects.get(pk=pk, company=company)
    except LLMProvider.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Deactivate all others in this company
    LLMProvider.objects.filter(company=company).update(is_active=False, is_default=False)
    provider.is_active = True
    provider.is_default = True
    provider.save(update_fields=["is_active", "is_default"])

    return Response(LLMProviderSerializer(provider).data)


@api_view(["POST"])
@throttle_classes([LLMTestThrottle])
def provider_test(request):
    """Test an LLM provider connection."""
    company = request.user.company
    serializer = LLMTestRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        provider = LLMProvider.objects.get(pk=serializer.validated_data["provider_id"], company=company)
    except LLMProvider.DoesNotExist:
        return Response({"error": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        llm = get_provider(provider)
        result = llm.chat([
            {"role": "user", "content": serializer.validated_data["message"]},
        ])
        return Response({
            "success": True,
            "response": result["content"],
            "model": result.get("model", provider.model_name),
            "tokens": result.get("prompt_tokens", 0) + result.get("completion_tokens", 0),
        })
    except Exception as e:
        return Response({
            "success": False,
            "error": str(e),
        }, status=status.HTTP_400_BAD_REQUEST)


# ─── Chat ────────────────────────────────────────────────────────

@api_view(["POST"])
@throttle_classes([LLMChatThrottle])
def chat(request):
    """Send a chat message and get an AI response."""
    company = request.user.company
    if not company:
        return Response({"error": "No company assigned"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = LLMChatRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    session_id = serializer.validated_data.get("session_id")
    feature = serializer.validated_data.get("feature", "chat")
    user_message = serializer.validated_data["message"]

    # Get or create session
    if session_id:
        try:
            session = LLMChatSession.objects.get(pk=session_id, company=company, user=request.user)
        except LLMChatSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
    else:
        session = LLMChatSession.objects.create(
            company=company,
            user=request.user,
            title=user_message[:100],
            feature=feature,
        )

    # Save user message
    LLMChatMessage.objects.create(session=session, role="user", content=user_message)

    # Build message history — cap at MAX_CHAT_HISTORY messages to prevent context overflow
    all_messages = session.messages.order_by("created_at")
    recent_messages = all_messages[max(0, all_messages.count() - MAX_CHAT_HISTORY):]
    messages = [{"role": msg.role, "content": msg.content} for msg in recent_messages]

    # Call LLM
    try:
        result = chat_completion(company, messages, feature=feature, user=request.user)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error("Chat completion failed: %s", e)
        return Response({"error": "LLM service unavailable"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Save assistant response
    assistant_msg = LLMChatMessage.objects.create(
        session=session,
        role="assistant",
        content=result["content"],
        metadata={"model": result.get("model"), "tokens": result.get("prompt_tokens", 0) + result.get("completion_tokens", 0)},
    )

    session.save(update_fields=["updated_at"])

    return Response({
        "session_id": session.id,
        "message": LLMChatMessageSerializer(assistant_msg).data,
        "usage": {
            "prompt_tokens": result.get("prompt_tokens", 0),
            "completion_tokens": result.get("completion_tokens", 0),
            "duration_ms": result.get("duration_ms", 0),
        },
    })


# ─── Sessions ────────────────────────────────────────────────────

@api_view(["GET"])
def session_list(request):
    """List chat sessions for the current user."""
    company = request.user.company
    sessions = LLMChatSession.objects.filter(company=company, user=request.user)[:20]
    return Response(LLMChatSessionSerializer(sessions, many=True).data)


@api_view(["GET"])
def session_detail(request, pk):
    """Get a chat session with all messages."""
    company = request.user.company
    try:
        session = LLMChatSession.objects.get(pk=pk, company=company, user=request.user)
    except LLMChatSession.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(LLMChatSessionSerializer(session).data)


@api_view(["DELETE"])
def session_delete(request, pk):
    """Delete a chat session."""
    company = request.user.company
    try:
        session = LLMChatSession.objects.get(pk=pk, company=company, user=request.user)
    except LLMChatSession.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    session.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Usage Stats ─────────────────────────────────────────────────

@api_view(["GET"])
def usage_stats(request):
    """Get LLM usage statistics for the company."""
    company = request.user.company
    if not company:
        return Response({"error": "No company assigned"}, status=status.HTTP_400_BAD_REQUEST)

    logs = LLMUsageLog.objects.filter(company=company)

    from django.db.models import Sum, Count, Avg
    stats = logs.aggregate(
        total_tokens=Sum("total_tokens"),
        total_requests=Count("id"),
        avg_duration=Avg("duration_ms"),
    )

    # Per-feature breakdown
    feature_stats = (
        logs.values("feature")
        .annotate(total=Sum("total_tokens"), count=Count("id"))
        .order_by("-total")
    )

    return Response({
        "total_tokens": stats["total_tokens"] or 0,
        "total_requests": stats["total_requests"] or 0,
        "avg_duration_ms": round(stats["avg_duration"] or 0, 1),
        "by_feature": list(feature_stats),
    })
