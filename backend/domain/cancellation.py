from models.workflow import WorkflowState


class WorkflowCancellationHandler:
    @staticmethod
    def cancel_workflow(state: WorkflowState, reason: str = "User cancelled execution") -> WorkflowState:
        state.status = "cancelled"
        state.error_message = reason

        for node in state.nodes:
            if node.status in ["planned", "ready", "executing", "awaiting_approval"]:
                node.status = "cancelled"
                node.error_message = reason

        state.pending_approval = None
        return state
