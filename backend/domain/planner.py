import uuid
from typing import Any
from models.workflow import WorkflowState, WorkflowNode, WorkflowEdge
from services.agent_registry import AgentRegistry, get_agent_registry


class WorkflowPlanner:
    """Creates the initial structured multi-agent workflow plan from user query."""

    def __init__(self, registry: AgentRegistry | None = None):
        self.registry = registry or get_agent_registry()

    def generate_initial_plan(
        self,
        query: str,
        workspace_id: str = "default_workspace",
        user_id: str = "default_user",
        initial_context: dict[str, Any] | None = None
    ) -> WorkflowState:
        workflow_id = f"wf-{uuid.uuid4().hex[:8]}"
        initial_context = initial_context or {}
        
        # Analyze query intent
        query_lower = query.lower()
        nodes: list[WorkflowNode] = []
        edges: list[WorkflowEdge] = []

        # Determine agent sequence based on query keywords or standard end-to-end SDLC pipeline
        include_ba = any(k in query_lower for k in ["brd", "requirement", "business", "stories", "spec", "platform", "system", "app"]) or True
        include_arch = any(k in query_lower for k in ["architect", "design", "c4", "diagram", "infra", "database", "platform", "system"]) or True
        include_po = any(k in query_lower for k in ["sprint", "backlog", "po", "product owner", "prioritize", "roadmap"])
        include_dev = any(k in query_lower for k in ["implement", "code", "dev", "develop", "task", "scaffold", "platform", "system"]) or True
        include_qe = any(k in query_lower for k in ["qa", "qe", "test", "quality", "strategy", "verify", "platform", "system"]) or True

        prev_node_id: str | None = None
        step_idx = 1

        if include_ba:
            ba_id = f"node-{step_idx}-ba"
            nodes.append(
                WorkflowNode(
                    id=ba_id,
                    agent_id="business-analyst",
                    task_type="dynamic_workflow_ba_task",
                    display_name="1. Business Requirements Analysis (BA)",
                    input_data={"prompt": query, **initial_context},
                    plan_version=1,
                    depends_on=[prev_node_id] if prev_node_id else [],
                    hitl_required=False,
                    position_x=50.0,
                    position_y=100.0
                )
            )
            if prev_node_id:
                edges.append(WorkflowEdge(id=f"edge-{prev_node_id}-{ba_id}", source=prev_node_id, target=ba_id, plan_version=1))
            prev_node_id = ba_id
            step_idx += 1

        if include_arch:
            arch_id = f"node-{step_idx}-arch"
            nodes.append(
                WorkflowNode(
                    id=arch_id,
                    agent_id="architect",
                    task_type="send_message",
                    display_name="2. System Architecture Design (Architect)",
                    input_data={"user_message": f"Design system architecture for: {query}"},
                    plan_version=1,
                    depends_on=[prev_node_id] if prev_node_id else [],
                    hitl_required=False,
                    position_x=330.0,
                    position_y=100.0
                )
            )
            if prev_node_id:
                edges.append(WorkflowEdge(id=f"edge-{prev_node_id}-{arch_id}", source=prev_node_id, target=arch_id, plan_version=1))
            prev_node_id = arch_id
            step_idx += 1

        if include_po:
            po_id = f"node-{step_idx}-po"
            nodes.append(
                WorkflowNode(
                    id=po_id,
                    agent_id="product-owner",
                    task_type="sprint_planning",
                    display_name=f"{step_idx}. Sprint Planning & Backlog (PO)",
                    input_data={"prompt": f"Sprint planning for: {query}"},
                    plan_version=1,
                    depends_on=[prev_node_id] if prev_node_id else [],
                    hitl_required=False,
                    position_x=610.0,
                    position_y=100.0
                )
            )
            if prev_node_id:
                edges.append(WorkflowEdge(id=f"edge-{prev_node_id}-{po_id}", source=prev_node_id, target=po_id, plan_version=1))
            prev_node_id = po_id
            step_idx += 1

        if include_dev:
            dev_id = f"node-{step_idx}-dev"
            nodes.append(
                WorkflowNode(
                    id=dev_id,
                    agent_id="developer",
                    task_type="handle_dev_message",
                    display_name=f"{step_idx}. Microservice Implementation (Dev)",
                    input_data={"message": f"Generate service implementation for: {query}"},
                    plan_version=1,
                    depends_on=[prev_node_id] if prev_node_id else [],
                    hitl_required=False,
                    position_x=890.0,
                    position_y=100.0
                )
            )
            if prev_node_id:
                edges.append(WorkflowEdge(id=f"edge-{prev_node_id}-{dev_id}", source=prev_node_id, target=dev_id, plan_version=1))
            prev_node_id = dev_id
            step_idx += 1

        if include_qe:
            qe_id = f"node-{step_idx}-qe"
            nodes.append(
                WorkflowNode(
                    id=qe_id,
                    agent_id="qe",
                    task_type="generate_test_strategy",
                    display_name=f"{step_idx}. Quality Strategy & Test Suite (QE)",
                    input_data={"requirements": query},
                    plan_version=1,
                    depends_on=[prev_node_id] if prev_node_id else [],
                    hitl_required=False,
                    position_x=1170.0,
                    position_y=100.0
                )
            )
            if prev_node_id:
                edges.append(WorkflowEdge(id=f"edge-{prev_node_id}-{qe_id}", source=prev_node_id, target=qe_id, plan_version=1))
            prev_node_id = qe_id

        # Mark first node as ready
        if nodes:
            nodes[0].status = "ready"

        return WorkflowState(
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            user_id=user_id,
            query=query,
            status="planned",
            plan_version=1,
            nodes=nodes,
            edges=edges,
            current_node_id=nodes[0].id if nodes else None,
            artifacts=[],
            replan_count=0,
            total_agent_invocations=0
        )


_planner_instance: WorkflowPlanner | None = None


def get_workflow_planner() -> WorkflowPlanner:
    global _planner_instance
    if _planner_instance is None:
        _planner_instance = WorkflowPlanner()
    return _planner_instance
