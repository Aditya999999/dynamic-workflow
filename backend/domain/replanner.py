import copy
import logging
from models.workflow import WorkflowState, WorkflowNode, WorkflowEdge, NextAction
from config.settings import get_settings
from models.errors import PolicyViolationError

logger = logging.getLogger(__name__)


class WorkflowReplanner:
    """Handles dynamic runtime workflow graph replanning when agents request feedback or additional iterations."""

    def __init__(self):
        self.settings = get_settings()

    def replan_on_feedback(
        self,
        state: WorkflowState,
        triggering_node_id: str,
        next_action: NextAction
    ) -> WorkflowState:
        """Dynamically inserts revision nodes into the existing DAG while preserving historical execution state."""
        if state.replan_count >= self.settings.dwf_max_replan_iterations:
            raise PolicyViolationError(
                f"Dynamic replan limit of {self.settings.dwf_max_replan_iterations} exceeded."
            )

        new_plan_version = state.plan_version + 1
        triggering_node = next((n for n in state.nodes if n.id == triggering_node_id), None)
        if not triggering_node:
            raise ValueError(f"Triggering node '{triggering_node_id}' not found in state.")

        logger.info(
            f"Dynamic replan triggered by node '{triggering_node_id}' requesting action '{next_action.type}' "
            f"on agent '{next_action.agent_id}'. New plan version: {new_plan_version}"
        )

        # Create revision nodes
        rev_count = state.replan_count + 1
        target_agent = next_action.agent_id or "business-analyst"
        target_task = next_action.task_type or "dynamic_workflow_ba_task"

        # 1. Revision Step (e.g., BA Revision)
        rev_node_1_id = f"node-rev{rev_count}-clarify-{target_agent[:3]}"
        rev_node_1 = WorkflowNode(
            id=rev_node_1_id,
            agent_id=target_agent,
            task_type=target_task,
            display_name=f"Revision {rev_count}: Clarification ({target_agent.title()})",
            input_data={
                "prompt": next_action.reason or "Address clarification requested by downstream agent",
                **(next_action.input_patch or {})
            },
            status="ready",
            plan_version=new_plan_version,
            depends_on=[triggering_node_id],
            position_x=triggering_node.position_x + 140.0,
            position_y=triggering_node.position_y + 120.0
        )

        # 2. Resumed Step (e.g., Architect Revision)
        rev_node_2_id = f"node-rev{rev_count}-resume-{triggering_node.agent_id[:4]}"
        rev_node_2 = WorkflowNode(
            id=rev_node_2_id,
            agent_id=triggering_node.agent_id,
            task_type=triggering_node.task_type,
            display_name=f"Revision {rev_count}: Re-evaluation ({triggering_node.agent_id.title()})",
            input_data={
                "user_message": f"Resume architecture design incorporating updated requirements from {rev_node_1_id}",
                "mock_scenario": "normal"  # On second pass, complete successfully
            },
            status="planned",
            plan_version=new_plan_version,
            depends_on=[rev_node_1_id],
            position_x=triggering_node.position_x + 280.0,
            position_y=triggering_node.position_y
        )

        # Rewire downstream dependents of triggering_node to depend on rev_node_2 instead
        downstream_nodes = [n for n in state.nodes if triggering_node_id in n.depends_on and n.id != rev_node_1_id]
        for dn in downstream_nodes:
            dn.depends_on = [rev_node_2_id if d == triggering_node_id else d for d in dn.depends_on]
            dn.position_x += 280.0

        # Remove old edges from triggering_node to downstream nodes
        state.edges = [e for e in state.edges if not (e.source == triggering_node_id and any(dn.id == e.target for dn in downstream_nodes))]

        # Add new nodes and edges
        state.nodes.extend([rev_node_1, rev_node_2])
        state.edges.append(
            WorkflowEdge(id=f"edge-{triggering_node_id}-{rev_node_1_id}", source=triggering_node_id, target=rev_node_1_id, plan_version=new_plan_version)
        )
        state.edges.append(
            WorkflowEdge(id=f"edge-{rev_node_1_id}-{rev_node_2_id}", source=rev_node_1_id, target=rev_node_2_id, plan_version=new_plan_version)
        )
        for dn in downstream_nodes:
            state.edges.append(
                WorkflowEdge(id=f"edge-{rev_node_2_id}-{dn.id}", source=rev_node_2_id, target=dn.id, plan_version=new_plan_version)
            )

        # Update state metadata
        state.plan_version = new_plan_version
        state.replan_count += 1
        state.current_node_id = rev_node_1_id

        return state


_replanner_instance: WorkflowReplanner | None = None


def get_workflow_replanner() -> WorkflowReplanner:
    global _replanner_instance
    if _replanner_instance is None:
        _replanner_instance = WorkflowReplanner()
    return _replanner_instance
