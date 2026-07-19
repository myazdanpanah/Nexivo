"""
Workflow Engine — Enterprise ERP Core.

Per WORKFLOW_ENGINE.md §1: Controls the lifecycle of every business document.
Per WORKFLOW_ENGINE.md §3: Centralized, Configuration Driven, Role Based, Event Driven, State Machine Based.
Per WORKFLOW_ENGINE.md §64: Business modules never implement their own workflow logic.

This is the foundation — a simplified state machine for document lifecycle.
Full implementation per WORKFLOW_ENGINE.md §58-60 will follow.
"""

import logging
from typing import Any, Dict, List, Optional
from enum import Enum

from django.db import transaction
from django.db.models import Model
from django.utils import timezone

from apps.finance.exceptions import ValidationError

logger = logging.getLogger(__name__)


class WorkflowState(str, Enum):
    """Document lifecycle states per WORKFLOW_ENGINE.md §8."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    CONFIRMED = "confirmed"
    POSTED = "posted"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class WorkflowTransition:
    """Represents a state transition in the workflow."""
    
    def __init__(
        self,
        from_state: WorkflowState,
        to_state: WorkflowState,
        action: str,
        required_role: Optional[str] = None,
        required_permission: Optional[str] = None,
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.action = action
        self.required_role = required_role
        self.required_permission = required_permission


# Standard transitions per WORKFLOW_ENGINE.md §12: State Lifecycle
DOCUMENT_TRANSITIONS = {
    "invoice": [
        WorkflowTransition(WorkflowState.DRAFT, WorkflowState.SUBMITTED, "submit"),
        WorkflowTransition(WorkflowState.SUBMITTED, WorkflowState.PENDING_APPROVAL, "approve"),
        WorkflowTransition(WorkflowState.PENDING_APPROVAL, WorkflowState.APPROVED, "confirm"),
        WorkflowTransition(WorkflowState.APPROVED, WorkflowState.POSTED, "post"),
        WorkflowTransition(WorkflowState.DRAFT, WorkflowState.CANCELLED, "cancel"),
        WorkflowTransition(WorkflowState.SUBMITTED, WorkflowState.REJECTED, "reject"),
    ],
    "voucher": [
        WorkflowTransition(WorkflowState.DRAFT, WorkflowState.SUBMITTED, "submit"),
        WorkflowTransition(WorkflowState.SUBMITTED, WorkflowState.CONFIRMED, "confirm"),
        WorkflowTransition(WorkflowState.DRAFT, WorkflowState.CANCELLED, "cancel"),
    ],
    "receipt": [
        WorkflowTransition(WorkflowState.DRAFT, WorkflowState.SUBMITTED, "submit"),
        WorkflowTransition(WorkflowState.SUBMITTED, WorkflowState.CONFIRMED, "confirm"),
        WorkflowTransition(WorkflowState.DRAFT, WorkflowState.CANCELLED, "cancel"),
    ],
    "payment": [
        WorkflowTransition(WorkflowState.DRAFT, WorkflowState.SUBMITTED, "submit"),
        WorkflowTransition(WorkflowState.SUBMITTED, WorkflowState.CONFIRMED, "confirm"),
        WorkflowTransition(WorkflowState.DRAFT, WorkflowState.CANCELLED, "cancel"),
    ],
}


class WorkflowEngine:
    """
    Centralized workflow engine for document lifecycle.
    
    Per WORKFLOW_ENGINE.md §36: Runtime Execution Engine.
    Per WORKFLOW_ENGINE.md §62: Runtime Execution Sequence.
    """

    @staticmethod
    def get_valid_transitions(document_type: str, current_state: str) -> List[Dict]:
        """Get all valid transitions from the current state."""
        transitions = DOCUMENT_TRANSITIONS.get(document_type, [])
        return [
            {
                "action": t.action,
                "from_state": t.from_state.value,
                "to_state": t.to_state.value,
                "required_role": t.required_role,
            }
            for t in transitions
            if t.from_state.value == current_state
        ]

    @staticmethod
    def validate_transition(
        document_type: str,
        current_state: str,
        action: str,
        user: Any = None,
    ) -> WorkflowTransition:
        """
        Validate that a transition is allowed.
        
        Per WORKFLOW_ENGINE.md §13: Transition Validation Pipeline.
        """
        transitions = DOCUMENT_TRANSITIONS.get(document_type, [])
        
        for t in transitions:
            if t.from_state.value == current_state and t.action == action:
                # Validate role if required
                if t.required_role and user:
                    if hasattr(user, "role") and user.role != t.required_role:
                        raise ValidationError(
                            f"Action '{action}' requires role '{t.required_role}'"
                        )
                return t
        
        raise ValidationError(
            f"Invalid transition: '{action}' from state '{current_state}' "
            f"for document type '{document_type}'"
        )

    @staticmethod
    @transaction.atomic
    def execute_transition(
        document: Model,
        document_type: str,
        action: str,
        user: Any,
        comment: str = "",
    ) -> Dict:
        """
        Execute a workflow transition on a document.
        
        Per WORKFLOW_ENGINE.md §62: 
        Load Workflow Instance → Validate Transition → Execute Transition → 
        Persist State → Write History → Publish Events.
        """
        current_state = getattr(document, "status", None)
        if not current_state:
            raise ValidationError("Document has no status field.")

        # Validate the transition
        transition = WorkflowEngine.validate_transition(
            document_type, current_state, action, user
        )

        # Execute the transition
        new_state = transition.to_state.value
        document.status = new_state
        document.save(update_fields=["status", "updated_at"])

        # Log the transition
        logger.info(
            f"Workflow: {document_type} #{document.pk} "
            f"transitioned from '{current_state}' to '{new_state}' "
            f"by {user.username} (action: {action})"
        )

        return {
            "document_type": document_type,
            "document_id": document.pk,
            "previous_state": current_state,
            "new_state": new_state,
            "action": action,
            "user": user.username if hasattr(user, "username") else str(user),
            "timestamp": timezone.now().isoformat(),
            "comment": comment,
        }

    @staticmethod
    def get_document_history(document_type: str, document_id: int) -> List[Dict]:
        """
        Get the workflow history for a document.
        
        Per WORKFLOW_ENGINE.md §31: Workflow History — immutable records.
        """
        # For now, return audit log entries
        # Full implementation will use dedicated workflow_history table
        return []  # Placeholder — will be implemented with workflow_history table
