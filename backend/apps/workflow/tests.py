"""
Workflow Engine Tests — per WORKFLOW_ENGINE.md §68: Completion Criteria.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.tests_helpers import create_test_company, create_test_user
from apps.finance.exceptions import ValidationError
from apps.manufacturing.models import ProductionOrder
from .models import (
    WorkflowDefinition, WorkflowState, WorkflowTransition,
    WorkflowInstance, WorkflowHistory,
)
from .service import WorkflowService, WorkflowExecutionService

User = get_user_model()


class WorkflowEngineTestBase(TestCase):
    """Shared setUp for workflow tests."""

    def setUp(self):
        self.company = create_test_company(name="WorkflowTestCo")
        self.user = create_test_user(username="wfuser", company=self.company, role="ceo")

        # Create a simple workflow: draft → submitted → approved → completed
        self.definition = WorkflowDefinition.objects.create(
            company=self.company,
            name="Simple Approval",
            document_type="production_order",
            version=1,
        )

        self.state_draft = WorkflowState.objects.create(
            definition=self.definition, name="draft", state_type="start", order=0,
        )
        self.state_submitted = WorkflowState.objects.create(
            definition=self.definition, name="submitted", state_type="normal", order=1,
        )
        self.state_approved = WorkflowState.objects.create(
            definition=self.definition, name="approved", state_type="approval", order=2,
        )
        self.state_completed = WorkflowState.objects.create(
            definition=self.definition, name="completed", state_type="completed", order=3,
        )
        self.state_cancelled = WorkflowState.objects.create(
            definition=self.definition, name="cancelled", state_type="cancelled", order=4,
        )
        self.state_rejected = WorkflowState.objects.create(
            definition=self.definition, name="rejected", state_type="rejected", order=5,
        )

        # Transitions
        WorkflowTransition.objects.create(
            definition=self.definition, source_state=self.state_draft,
            target_state=self.state_submitted, action="submit",
        )
        WorkflowTransition.objects.create(
            definition=self.definition, source_state=self.state_submitted,
            target_state=self.state_approved, action="approve",
        )
        WorkflowTransition.objects.create(
            definition=self.definition, source_state=self.state_approved,
            target_state=self.state_completed, action="complete",
        )
        WorkflowTransition.objects.create(
            definition=self.definition, source_state=self.state_submitted,
            target_state=self.state_rejected, action="reject", requires_comment=True,
        )
        WorkflowTransition.objects.create(
            definition=self.definition, source_state=self.state_draft,
            target_state=self.state_cancelled, action="cancel",
        )

        # A test production order to attach workflow to
        self.po = ProductionOrder.objects.create(
            company=self.company, number="PO-WF-001",
            product_name="Widget", quantity=100, status="draft",
        )


class StartWorkflowTests(WorkflowEngineTestBase):
    """Tests for starting workflows."""

    def test_start_workflow(self):
        instance = WorkflowService.start_workflow(
            company=self.company,
            document_type="production_order",
            document_id=self.po.id,
            user=self.user,
        )
        self.assertEqual(instance.status, "active")
        self.assertEqual(instance.current_state.name, "draft")

    def test_start_workflow_creates_history(self):
        instance = WorkflowService.start_workflow(
            company=self.company,
            document_type="production_order",
            document_id=self.po.id,
            user=self.user,
        )
        history = WorkflowHistory.objects.filter(instance=instance)
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().action, "started")

    def test_start_workflow_no_definition_raises(self):
        with self.assertRaises(ValidationError):
            WorkflowService.start_workflow(
                company=self.company,
                document_type="nonexistent",
                document_id=999,
                user=self.user,
            )


class TransitionTests(WorkflowEngineTestBase):
    """Tests for executing transitions."""

    def _start(self):
        return WorkflowService.start_workflow(
            company=self.company,
            document_type="production_order",
            document_id=self.po.id,
            user=self.user,
        )

    def test_draft_to_submitted(self):
        instance = self._start()
        instance = WorkflowExecutionService.execute_transition(
            instance, "submit", self.user,
        )
        self.assertEqual(instance.current_state.name, "submitted")
        self.assertEqual(instance.status, "active")

    def test_full_lifecycle(self):
        instance = self._start()
        instance = WorkflowExecutionService.execute_transition(instance, "submit", self.user)
        instance = WorkflowExecutionService.execute_transition(instance, "approve", self.user)
        instance = WorkflowExecutionService.execute_transition(instance, "complete", self.user)
        self.assertEqual(instance.current_state.name, "completed")
        self.assertEqual(instance.status, "completed")

    def test_invalid_transition_raises(self):
        instance = self._start()
        with self.assertRaises(ValidationError):
            WorkflowExecutionService.execute_transition(instance, "approve", self.user)

    def test_reject_requires_comment(self):
        instance = self._start()
        instance = WorkflowExecutionService.execute_transition(instance, "submit", self.user)
        with self.assertRaises(ValidationError):
            WorkflowExecutionService.execute_transition(instance, "reject", self.user)
        instance = WorkflowExecutionService.execute_transition(
            instance, "reject", self.user, comment="Not enough info",
        )
        self.assertEqual(instance.status, "rejected")

    def test_cancel_workflow(self):
        instance = self._start()
        instance = WorkflowExecutionService.cancel_workflow(
            instance, self.user, reason="No longer needed",
        )
        self.assertEqual(instance.status, "cancelled")

    def test_cannot_transition_completed(self):
        instance = self._start()
        instance = WorkflowExecutionService.execute_transition(instance, "submit", self.user)
        instance = WorkflowExecutionService.execute_transition(instance, "approve", self.user)
        instance = WorkflowExecutionService.execute_transition(instance, "complete", self.user)
        with self.assertRaises(ValidationError):
            WorkflowExecutionService.execute_transition(instance, "submit", self.user)

    def test_history_recorded(self):
        instance = self._start()
        instance = WorkflowExecutionService.execute_transition(instance, "submit", self.user, comment="Please review")
        history = WorkflowHistory.objects.filter(instance=instance).order_by("timestamp")
        self.assertEqual(history.count(), 2)  # started + submit
        self.assertEqual(history.last().action, "submit")
        self.assertEqual(history.last().comment, "Please review")

    def test_available_actions(self):
        instance = self._start()
        actions = WorkflowService.get_available_actions(instance)
        self.assertEqual(len(actions), 2)  # submit, cancel
        action_names = [a["action"] for a in actions]
        self.assertIn("submit", action_names)
        self.assertIn("cancel", action_names)
