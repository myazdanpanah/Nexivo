"""Workflow Engine admin registration."""
from django.contrib import admin
from .models import (
    WorkflowDefinition, WorkflowState, WorkflowTransition,
    WorkflowRule, WorkflowInstance, WorkflowHistory, WorkflowComment,
)


class WorkflowStateInline(admin.TabularInline):
    model = WorkflowState
    extra = 0


class WorkflowTransitionInline(admin.TabularInline):
    model = WorkflowTransition
    fk_name = "definition"
    extra = 0


@admin.register(WorkflowDefinition)
class WorkflowDefinitionAdmin(admin.ModelAdmin):
    list_display = ["name", "document_type", "version", "is_active"]
    list_filter = ["document_type", "is_active"]
    inlines = [WorkflowStateInline, WorkflowTransitionInline]


@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    list_display = ["id", "document_type", "document_id", "current_state", "status"]
    list_filter = ["document_type", "status"]


@admin.register(WorkflowHistory)
class WorkflowHistoryAdmin(admin.ModelAdmin):
    list_display = ["instance", "action", "performed_by", "timestamp"]
    list_filter = ["action"]
    readonly_fields = ["instance", "previous_state", "new_state", "action", "performed_by", "comment", "timestamp"]
