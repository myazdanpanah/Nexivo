"""
Workflow Engine Views — REST API per WORKFLOW_ENGINE.md §43.
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.core.responses import (
    success_response, error_response, business_rule_error,
    not_found_response, forbidden_response,
)

from .models import (
    WorkflowDefinition, WorkflowInstance, WorkflowHistory, WorkflowComment,
)
from .service import WorkflowService, WorkflowExecutionService


@api_view(["GET"])
def workflow_list(request):
    """List workflow instances for the company."""
    instances = WorkflowService.get_pending_workflows(request.user.company)
    data = [
        {
            "id": inst.id,
            "document_type": inst.document_type,
            "document_id": inst.document_id,
            "current_state": inst.current_state.name,
            "status": inst.status,
            "assigned_to": inst.assigned_to.username if inst.assigned_to else None,
            "created_at": inst.created_at.isoformat(),
        }
        for inst in instances
    ]
    return success_response(data=data)


@api_view(["GET"])
def workflow_detail(request, pk):
    """Get workflow instance details with history."""
    try:
        instance = WorkflowInstance.objects.get(pk=pk, company=request.user.company)
    except WorkflowInstance.DoesNotExist:
        return not_found_response("Workflow instance not found")

    history = WorkflowHistory.objects.filter(instance=instance).select_related(
        "previous_state", "new_state", "performed_by"
    )
    actions = WorkflowService.get_available_actions(instance)

    return success_response(data={
        "id": instance.id,
        "document_type": instance.document_type,
        "document_id": instance.document_id,
        "current_state": instance.current_state.name,
        "status": instance.status,
        "available_actions": actions,
        "history": [
            {
                "action": h.action,
                "from_state": h.previous_state.name if h.previous_state else None,
                "to_state": h.new_state.name if h.new_state else None,
                "performed_by": h.performed_by.username if h.performed_by else None,
                "comment": h.comment,
                "timestamp": h.timestamp.isoformat(),
            }
            for h in history
        ],
    })


@api_view(["POST"])
def workflow_transition(request, pk):
    """Execute a workflow transition."""
    try:
        instance = WorkflowInstance.objects.get(pk=pk, company=request.user.company)
    except WorkflowInstance.DoesNotExist:
        return not_found_response("Workflow instance not found")

    action = request.data.get("action")
    comment = request.data.get("comment", "")

    if not action:
        return error_response("Action is required", status_code=400)

    try:
        instance = WorkflowExecutionService.execute_transition(
            instance=instance,
            action=action,
            user=request.user,
            comment=comment,
        )
        return success_response(
            data={
                "id": instance.id,
                "current_state": instance.current_state.name,
                "status": instance.status,
            },
            message=f"Transition '{action}' executed",
        )
    except Exception as e:
        return business_rule_error(str(e))


@api_view(["POST"])
def workflow_cancel(request, pk):
    """Cancel a workflow instance."""
    try:
        instance = WorkflowInstance.objects.get(pk=pk, company=request.user.company)
    except WorkflowInstance.DoesNotExist:
        return not_found_response("Workflow instance not found")

    reason = request.data.get("reason", "")
    try:
        instance = WorkflowExecutionService.cancel_workflow(
            instance=instance, user=request.user, reason=reason,
        )
        return success_response(
            data={"id": instance.id, "status": instance.status},
            message="Workflow cancelled",
        )
    except Exception as e:
        return business_rule_error(str(e))


@api_view(["GET"])
def workflow_pending(request):
    """List workflows pending the current user's action."""
    instances = WorkflowService.get_pending_workflows(request.user.company, user=request.user)
    data = [
        {
            "id": inst.id,
            "document_type": inst.document_type,
            "document_id": inst.document_id,
            "current_state": inst.current_state.name,
            "available_actions": [
                t["action"]
                for t in WorkflowService.get_available_actions(inst)
            ],
        }
        for inst in instances
    ]
    return success_response(data=data)


@api_view(["GET"])
def workflow_definitions(request):
    """List workflow definitions for the company."""
    defs = WorkflowDefinition.objects.filter(company=request.user.company, is_active=True)
    data = [
        {
            "id": d.id,
            "name": d.name,
            "document_type": d.document_type,
            "version": d.version,
        }
        for d in defs
    ]
    return success_response(data=data)
