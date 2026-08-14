import uuid
from typing import Any
from models.workflow import WorkflowState, WorkflowNode
from models.hitl import PendingApproval, ApprovalResolution


class HITLManager:
    """Manages Human-In-The-Loop interrupt creation and approval resolution."""

    @staticmethod
    def create_pending_approval(
        node: WorkflowNode,
        reason: str,
        artifact_id: str | None = None,
        artifact_summary: str | None = None,
        proposed_output: dict[str, Any] | None = None
    ) -> PendingApproval:
        return PendingApproval(
            approval_id=f"appr-{uuid.uuid4().hex[:8]}",
            node_id=node.id,
            agent_id=node.agent_id,
            task_type=node.task_type,
            reason=reason,
            artifact_id=artifact_id,
            artifact_summary=artifact_summary,
            proposed_output=proposed_output or node.output_data,
            feedback_requested="Review the generated requirements/artifact and approve or request adjustments."
        )

    @staticmethod
    def apply_approval_decision(
        state: WorkflowState,
        resolution: ApprovalResolution
    ) -> WorkflowState:
        if not state.pending_approval:
            raise ValueError(f"Workflow {state.workflow_id} has no pending approval.")

        pending_node_id = state.pending_approval.node_id
        target_node = next((n for n in state.nodes if n.id == pending_node_id), None)
        if not target_node:
            raise ValueError(f"Node {pending_node_id} associated with approval not found.")

        if resolution.decision == "approved":
            target_node.status = "completed"
            state.pending_approval = None
            state.status = "executing"
        elif resolution.decision == "edited":
            if resolution.edited_data:
                target_node.output_data.update(resolution.edited_data)
            target_node.status = "completed"
            state.pending_approval = None
            state.status = "executing"
        elif resolution.decision == "rejected":
            target_node.status = "failed"
            target_node.error_message = f"Rejected by human reviewer: {resolution.feedback or 'No feedback provided'}"
            state.pending_approval = None
            state.status = "failed"

        return state
