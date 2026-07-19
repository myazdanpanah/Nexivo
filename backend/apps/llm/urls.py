from django.urls import path
from . import views

urlpatterns = [
    # Provider management
    path("providers/", views.provider_list, name="llm-provider-list"),
    path("providers/<int:pk>/", views.provider_detail, name="llm-provider-detail"),
    path("providers/<int:pk>/activate/", views.provider_set_active, name="llm-provider-activate"),
    path("providers/test/", views.provider_test, name="llm-provider-test"),
    # Chat
    path("chat/", views.chat, name="llm-chat"),
    path("sessions/", views.session_list, name="llm-session-list"),
    path("sessions/<int:pk>/", views.session_detail, name="llm-session-detail"),
    path("sessions/<int:pk>/delete/", views.session_delete, name="llm-session-delete"),
    # Usage
    path("usage/", views.usage_stats, name="llm-usage-stats"),
]
