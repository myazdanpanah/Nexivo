"""
Workflow Engine Service — per WORKFLOW_ENGINE.md §61: Core Services.

Provides:
- WorkflowService: Primary orchestration
- WorkflowExecutionService: Executes transitions
- Creates history records, validates transitions, manages state changes
"""

import logging
from typing import Dict, Optional

from django.db import transaction
from django.utils import timezone

from apps.finance.exceptions import ValidationError
from .models import (
    WorkflowDefinition, WorkflowState, WorkflowTransition,
    WorkflowInstance, WorkflowHistory, WorkflowComment,
)

logger = logging.getLogger(__name__)


class WorkflowService:
    """
    Primary orchestration layer for workflow operations.
    Per WORKFLOW_ENGINE.md §61: WorkflowService.
    """

    @staticmethod
    def start_workflow(
        company,
        document_type: str,
        document_id: int,
        user,
    ) -> WorkflowInstance:
        """
        Start a new workflow for a document.
        Per WORKFLOW_ENGINE.md §36: Runtime Execution Engine.
        """
        # Find the active workflow definition for this document type
        definition = WorkflowDefinition.objects.filter(
            company=company,
            document_type=document_type,
            is_active=True,
        ).first()

        if not definition:
            raise ValidationError(f"No active workflow definition for '{document_type}'")

        # Find the start state
        start_state = definition.states.filter(state_type="start").first()
        if not start_state:
            raise ValidationError(f"No start state defined for workflow '{definition.name}'")

        # Create workflow instance
        instance = WorkflowInstance.objects.create(
            company=company,
            definition=definition,
            current_state=start_state,
            document_type=document_type,
            document_id=document_id,
            status="active",
        )

        # Record history
        WorkflowHistory.objects.create(
            instance=instance,
            previous_state=None,
            new_state=start_state,
            action="started",
            performed_by=user,
            comment="Workflow started",
        )

        logger.info(f"Workflow started: {instance}")
        return instance

    @staticmethod
    def get_available_actions(instance: WorkflowInstance) -> list:
        """Get all actions available from the current state."""
        transitions = WorkflowTransition.objects.filter(
            definition=instance.definition,
            source_state=instance.current_state,
        )
        return [
            {
                "action": t.action,
                "target_state": t.target_state.name,
                "requires_comment": t.requires_comment,
            }
            for t in transitions
        ]

    @staticmethod
    def get_pending_workflows(company, user=None):
        """Get all active workflow instances pending action."""
        qs = WorkflowInstance.objects.filter(
            company=company,
            status="active",
        ).select_related("current_state", "definition", "assigned_to")

        if user:
            qs = qs.filter(assigned_to=user)

        return qs


class WorkflowExecutionService:
    """
    Executes workflow transitions.
    Per WORKFLOW_ENGINE.md §61: WorkflowExecutionService.
    Per WORKFLOW_ENGINE.md §62: Runtime Execution Sequence.
    """

    @staticmethod
    @transaction.atomic
    def execute_transition(
        instance: WorkflowInstance,
        action: str,
        user,
        comment: str = "",
    ) -> WorkflowInstance:
        """
        Execute a workflow transition.
        Per WORKFLOW_ENGINE.md §62: Full execution sequence.
        """
        # 1. Validate instance is active
        if instance.status != "active":
            raise ValidationError(f"Workflow is {instance.status}, cannot execute transitions")

        # 2. Find the transition
        transition = WorkflowTransition.objects.filter(
            definition=instance.definition,
            source_state=instance.current_state,
            action=action,
        ).first()

        if not transition:
            raise ValidationError(
                f"Action '{action}' not available from state '{instance.current_state.name}'"
            )

        # 3. Validate required comment
        if transition.requires_comment and not comment:
            raise ValidationError(f"Comment is required for action '{action}'")

        # 4. Check role permission (simplified)
        if transition.target_state.required_role:
            instance.assigned_role = transition.target_state.required_role

        # 5. Execute transition
        previous_state = instance.current_state
        instance.current_state = transition.target_state
        instance.updated_at = timezone.now()

        # Update status based on target state type
        if transition.target_state.state_type == "completed":
            instance.status = "completed"
        elif transition.target_state.state_type == "cancelled":
            instance.status = "cancelled"
        elif transition.target_state.state_type == "rejected":
            instance.status = "rejected"

        instance.save()

        # 6. Record history
        WorkflowHistory.objects.create(
            instance=instance,
            previous_state=previous_state,
            new_state=transition.target_state,
            action=action,
            performed_by=user,
            comment=comment,
        )

        # 7. Record comment if provided
        if comment:
            WorkflowComment.objects.create(
                instance=instance,
                author=user,
                text=comment,
            )

        logger.info(
            f"Workflow transition: {instance.document_type}#{instance.document_id} "
            f"{previous_state.name} → {transition.target_state.name} ({action}) by {user.username}"
        )

        return instance

    @staticmethod
    @transaction.atomic
    def cancel_workflow(
        instance: WorkflowInstance,
        user,
        reason: str = "",
    ) -> WorkflowInstance:
        """Cancel a workflow instance."""
        if instance.status != "active":
            raise ValidationError(f"Workflow is already {instance.status}")

        previous_state = instance.current_state
        cancel_state = WorkflowState.objects.filter(
            definition=instance.definition,
            state_type="cancelled",
        ).first()

        if cancel_state:
            instance.current_state = cancel_state

        instance.status = "cancelled"
        instance.save()

        WorkflowHistory.objects.create(
            instance=instance,
            previous_state=previous_state,
            new_state=cancel_state,
            action="cancel",
            performed_by=user,
            comment=reason or "Workflow cancelled",
        )

        logger.info(f"Workflow cancelled: {instance}")
        return instance
