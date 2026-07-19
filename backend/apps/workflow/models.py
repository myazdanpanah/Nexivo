"""
Workflow Engine Models — per WORKFLOW_ENGINE.md §58: Database Model.

Configuration Tables:
- WorkflowDefinition: Workflow template (draft → submitted → approved → executed)
- WorkflowState: Each state with allowed actions and required role
- WorkflowTransition: State transitions with validation rules
- WorkflowRule: Business rules for conditional routing

Runtime Tables:
- WorkflowInstance: One per document, tracks current state
- WorkflowHistory: Immutable audit trail of every transition
- WorkflowComment: Comments on workflow actions
"""

from django.db import models
from django.conf import settings


# ─── Workflow Configuration ───────────────────────────────────

class WorkflowDefinition(models.Model):
    """
    Workflow definition — describes the lifecycle of a document.
    Per WORKFLOW_ENGINE.md §6: Workflow Definition.
    """
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="workflow_definitions")
    name = models.CharField(max_length=200, help_text="e.g. Purchase Order Approval")
    document_type = models.CharField(max_length=50, help_text="e.g. invoice, purchase_order, production_order")
    description = models.TextField(blank=True, default="")
    version = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("company", "document_type", "version")]
        ordering = ["document_type", "-version"]

    def __str__(self):
        return f"{self.name} v{self.version} ({self.document_type})"


class WorkflowState(models.Model):
    """
    A state in a workflow definition.
    Per WORKFLOW_ENGINE.md §8: Workflow State.
    Per WORKFLOW_ENGINE.md §9: State Types.
    """
    STATE_TYPES = [
        ("start", "Start"),
        ("normal", "Normal"),
        ("approval", "Approval"),
        ("review", "Review"),
        ("waiting", "Waiting"),
        ("automated", "Automated"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("rejected", "Rejected"),
    ]

    definition = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name="states")
    name = models.CharField(max_length=100, help_text="e.g. draft, submitted, manager_approval")
    state_type = models.CharField(max_length=20, choices=STATE_TYPES, default="normal")
    required_role = models.CharField(max_length=50, blank=True, default="",
                                      help_text="Role required to act in this state")
    description = models.TextField(blank=True, default="")
    order = models.IntegerField(default=0, help_text="Display order")

    class Meta:
        ordering = ["order"]
        unique_together = [("definition", "name")]

    def __str__(self):
        return f"{self.name} ({self.state_type})"


class WorkflowTransition(models.Model):
    """
    A transition between two states.
    Per WORKFLOW_ENGINE.md §10: Transition.
    """
    definition = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name="transitions")
    source_state = models.ForeignKey(WorkflowState, on_delete=models.CASCADE, related_name="outgoing_transitions")
    target_state = models.ForeignKey(WorkflowState, on_delete=models.CASCADE, related_name="incoming_transitions")
    action = models.CharField(max_length=50, help_text="e.g. submit, approve, reject, cancel")
    description = models.TextField(blank=True, default="")
    requires_comment = models.BooleanField(default=False, help_text="Mandatory comment on this transition?")
    auto_execute = models.BooleanField(default=False, help_text="Execute automatically without user action?")

    class Meta:
        ordering = ["action"]
        unique_together = [("definition", "source_state", "action")]

    def __str__(self):
        return f"{self.source_state.name} → {self.target_state.name} ({self.action})"


class WorkflowRule(models.Model):
    """
    Business rule for conditional routing.
    Per WORKFLOW_ENGINE.md §14: Rule Engine.
    Per WORKFLOW_ENGINE.md §15: Conditional Routing.
    """
    RULE_TYPES = [
        ("amount_threshold", "Amount Threshold"),
        ("role_check", "Role Check"),
        ("field_value", "Field Value"),
        ("custom", "Custom Expression"),
    ]

    definition = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name="rules")
    transition = models.ForeignKey(WorkflowTransition, on_delete=models.CASCADE, related_name="rules", null=True, blank=True)
    name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=30, choices=RULE_TYPES)
    condition = models.JSONField(default=dict, help_text="JSON condition, e.g. {'field': 'total', 'operator': '>', 'value': 5000000}")
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-priority"]

    def __str__(self):
        return self.name


# ─── Workflow Runtime ─────────────────────────────────────────

class WorkflowInstance(models.Model):
    """
    Runtime workflow instance — one per document.
    Per WORKFLOW_ENGINE.md §7: Workflow Instance.
    """
    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("rejected", "Rejected"),
    ]

    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="workflow_instances")
    definition = models.ForeignKey(WorkflowDefinition, on_delete=models.PROTECT, related_name="instances")
    current_state = models.ForeignKey(WorkflowState, on_delete=models.PROTECT, related_name="active_instances")

    # Document reference
    document_type = models.CharField(max_length=50)
    document_id = models.BigIntegerField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="assigned_workflows")
    assigned_role = models.CharField(max_length=50, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Workflow #{self.id}: {self.document_type}#{self.document_id} → {self.current_state.name}"


class WorkflowHistory(models.Model):
    """
    Immutable audit trail of every workflow transition.
    Per WORKFLOW_ENGINE.md §31: Workflow History.
    """
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name="history")
    previous_state = models.ForeignKey(WorkflowState, on_delete=models.SET_NULL, null=True, related_name="history_from")
    new_state = models.ForeignKey(WorkflowState, on_delete=models.SET_NULL, null=True, related_name="history_to")
    action = models.CharField(max_length=50)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    comment = models.TextField(blank=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action}: {self.previous_state} → {self.new_state} by {self.performed_by}"


class WorkflowComment(models.Model):
    """
    Comments on workflow actions.
    Per WORKFLOW_ENGINE.md §23: Approval Comments.
    """
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.instance}"
