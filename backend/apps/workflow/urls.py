"""
Workflow Engine URL Patterns.
Per WORKFLOW_ENGINE.md §43: Workflow API.
"""
from django.urls import path
from . import views

urlpatterns = [
    path("", views.workflow_list, name="workflow-list"),
    path("definitions/", views.workflow_definitions, name="workflow-definitions"),
    path("pending/", views.workflow_pending, name="workflow-pending"),
    path("<int:pk>/", views.workflow_detail, name="workflow-detail"),
    path("<int:pk>/transition/", views.workflow_transition, name="workflow-transition"),
    path("<int:pk>/cancel/", views.workflow_cancel, name="workflow-cancel"),
]
