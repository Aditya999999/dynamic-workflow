import logging
from typing import Any
from models.workflow import WorkflowState, WorkflowNode
from models.errors import PolicyViolationError
from services.agent_registry import AgentRegistry, get_agent_registry
from config.settings import get_settings

logger = logging.getLogger(__name__)


class OrchestrationPolicy:
    def __init__(self, registry: AgentRegistry | None = None):
        self.settings = get_settings()
        self.registry = registry or get_agent_registry()

    def validate_workflow_limits(self, state: WorkflowState) -> None:
        """Validates global workflow guardrails."""
        if state.status == "cancelled":
            raise PolicyViolationError("Workflow is cancelled and cannot execute further steps.")

        if len(state.nodes) > self.settings.dwf_max_workflow_nodes:
            raise PolicyViolationError(
                f"Maximum workflow nodes limit ({self.settings.dwf_max_workflow_nodes}) exceeded. Current: {len(state.nodes)}"
            )

        if state.replan_count > self.settings.dwf_max_replan_iterations:
            raise PolicyViolationError(
                f"Maximum dynamic replan limit ({self.settings.dwf_max_replan_iterations}) exceeded. Current: {state.replan_count}"
            )

        if state.total_agent_invocations >= self.settings.dwf_max_total_agent_invocations:
            raise PolicyViolationError(
                f"Maximum total agent invocations ({self.settings.dwf_max_total_agent_invocations}) reached."
            )

    def validate_node_invocation(self, state: WorkflowState, node: WorkflowNode) -> None:
        """Validates that a specific node is eligible for execution under policy constraints."""
        self.validate_workflow_limits(state)

        # 1. Check agent existence
        agent = self.registry.get_agent(node.agent_id)
        if not agent:
            raise PolicyViolationError(f"Agent '{node.agent_id}' is not registered in agent registry.")

        if not agent.invocation_enabled or agent.status != "active":
            raise PolicyViolationError(f"Agent '{node.agent_id}' is currently disabled or inactive.")

        # 2. Check task type support
        if not self.registry.supports_task(node.agent_id, node.task_type):
            raise PolicyViolationError(
                f"Task type '{node.task_type}' is not supported by agent '{node.agent_id}'."
            )

        # 3. Check per-node invocation count limit
        if node.invocation_count >= self.settings.dwf_max_agent_reinvocations:
            raise PolicyViolationError(
                f"Node '{node.id}' reached max reinvocation limit ({self.settings.dwf_max_agent_reinvocations})."
            )

        # 4. Check dependencies
        for dep_id in node.depends_on:
            dep_node = next((n for n in state.nodes if n.id == dep_id), None)
            if not dep_node:
                raise PolicyViolationError(f"Dependency node '{dep_id}' not found in workflow state.")
            if dep_node.status != "completed":
                raise PolicyViolationError(
                    f"Dependency '{dep_id}' (status: {dep_node.status}) must be completed before '{node.id}' can execute."
                )

        # 5. Check graph cycles
        if self.detect_cycle(state):
            raise PolicyViolationError("Cycle detected in workflow dependency graph.")

    def detect_cycle(self, state: WorkflowState) -> bool:
        """Detects if any circular dependencies exist in the workflow graph."""
        adj: dict[str, list[str]] = {n.id: [] for n in state.nodes}
        for edge in state.edges:
            if edge.source in adj and edge.target in adj:
                adj[edge.source].append(edge.target)

        visited: dict[str, int] = {n.id: 0 for n in state.nodes}  # 0: unvisited, 1: visiting, 2: visited

        def dfs(node_id: str) -> bool:
            visited[node_id] = 1
            for neighbor in adj.get(node_id, []):
                if visited[neighbor] == 1:
                    return True
                if visited[neighbor] == 0 and dfs(neighbor):
                    return True
            visited[node_id] = 2
            return False

        for node in state.nodes:
            if visited[node.id] == 0:
                if dfs(node.id):
                    return True
        return False


_policy_instance: OrchestrationPolicy | None = None


def get_orchestration_policy() -> OrchestrationPolicy:
    global _policy_instance
    if _policy_instance is None:
        _policy_instance = OrchestrationPolicy()
    return _policy_instance
