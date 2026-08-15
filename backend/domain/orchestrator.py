import asyncio
import logging
from datetime import datetime
from typing import Any

from models.workflow import WorkflowState, WorkflowNode, WorkflowExecutionResponse
from models.events import WorkflowEvent
from models.hitl import PendingApproval, ApprovalResolution
from models.errors import WorkflowError, PolicyViolationError, AgentExecutionError

from domain.planner import WorkflowPlanner, get_workflow_planner
from domain.replanner import WorkflowReplanner, get_workflow_replanner
from domain.orchestration_policy import OrchestrationPolicy, get_orchestration_policy
from domain.hitl import HITLManager
from domain.cancellation import WorkflowCancellationHandler
from domain.deep_agent import DeepAgentService, get_deep_agent_service
from services.workflow_repository import WorkflowRepository, get_workflow_repository
from services.event_repository import EventRepository, get_event_repository
from services.artifact_store import ArtifactStore, get_artifact_store
from services.event_stream import EventStreamBroker, get_event_stream_broker

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    def __init__(
        self,
        planner: WorkflowPlanner | None = None,
        replanner: WorkflowReplanner | None = None,
        policy: OrchestrationPolicy | None = None,
        deep_agent: DeepAgentService | None = None,
        wf_repo: WorkflowRepository | None = None,
        event_repo: EventRepository | None = None,
        artifact_store: ArtifactStore | None = None,
        stream_broker: EventStreamBroker | None = None
    ):
        self.planner = planner or get_workflow_planner()
        self.replanner = replanner or get_workflow_replanner()
        self.policy = policy or get_orchestration_policy()
        self.deep_agent = deep_agent or get_deep_agent_service()
        self.wf_repo = wf_repo or get_workflow_repository()
        self.event_repo = event_repo or get_event_repository()
        self.artifact_store = artifact_store or get_artifact_store()
        self.stream_broker = stream_broker or get_event_stream_broker()

    async def emit_event(
        self,
        workflow_id: str,
        event_type: str,
        node_id: str | None = None,
        agent_id: str | None = None,
        payload: dict[str, Any] | None = None
    ) -> WorkflowEvent:
        seq = await self.event_repo.get_next_sequence_number(workflow_id)
        event = WorkflowEvent(
            workflow_id=workflow_id,
            sequence_number=seq,
            event_type=event_type,  # type: ignore
            node_id=node_id,
            agent_id=agent_id,
            payload=payload or {}
        )
        await self.stream_broker.broadcast(event)
        return event

    async def create_and_plan_workflow(
        self,
        query: str,
        workspace_id: str = "default_workspace",
        user_id: str = "default_user",
        initial_context: dict[str, Any] | None = None
    ) -> WorkflowState:
        state = self.planner.generate_initial_plan(
            query=query,
            workspace_id=workspace_id,
            user_id=user_id,
            initial_context=initial_context
        )

        await self.wf_repo.save_workflow(state)

        await self.emit_event(
            workflow_id=state.workflow_id,
            event_type="workflow_created",
            payload={"query": query, "workspace_id": workspace_id, "user_id": user_id}
        )

        await self.emit_event(
            workflow_id=state.workflow_id,
            event_type="plan_created",
            payload={
                "plan_version": state.plan_version,
                "node_count": len(state.nodes),
                "nodes": [n.model_dump(mode="json") for n in state.nodes]
            }
        )

        return state

    async def execute_workflow_async(self, workflow_id: str, auto_approve_hitl: bool = False) -> None:
        """Launches the execution loop in the background."""
        asyncio.create_task(self._run_execution_loop(workflow_id, auto_approve_hitl))

    async def _run_execution_loop(self, workflow_id: str, auto_approve_hitl: bool = False) -> None:
        state = await self.wf_repo.get_workflow(workflow_id)
        if not state:
            logger.error(f"Workflow {workflow_id} not found for execution.")
            return

        state.status = "executing"
        await self.wf_repo.save_workflow(state)

        try:
            while True:
                # Refresh state from repository
                state = await self.wf_repo.get_workflow(workflow_id)
                if not state or state.status in ["completed", "failed", "cancelled", "awaiting_approval"]:
                    break

                # Find the next ready node
                next_node = self._find_next_executable_node(state)
                if not next_node:
                    # Check if all completed
                    if all(n.status == "completed" for n in state.nodes):
                        state.status = "completed"
                        await self.wf_repo.save_workflow(state)
                        await self.emit_event(
                            workflow_id=workflow_id,
                            event_type="workflow_completed",
                            payload={"message": "All workflow tasks completed successfully."}
                        )
                    elif any(n.status == "failed" for n in state.nodes):
                        state.status = "failed"
                        await self.wf_repo.save_workflow(state)
                        await self.emit_event(
                            workflow_id=workflow_id,
                            event_type="workflow_failed",
                            payload={"error": state.error_message or "One or more nodes failed."}
                        )
                    break

                # Execute this node
                await self._execute_node(state, next_node, auto_approve_hitl)

        except Exception as e:
            logger.exception(f"Fatal error during workflow {workflow_id} execution: {e}")
            if state:
                state.status = "failed"
                state.error_message = str(e)
                await self.wf_repo.save_workflow(state)
                await self.emit_event(
                    workflow_id=workflow_id,
                    event_type="workflow_failed",
                    payload={"error": str(e)}
                )

    def _find_next_executable_node(self, state: WorkflowState) -> WorkflowNode | None:
        for node in state.nodes:
            if node.status == "ready":
                return node
            if node.status == "planned":
                # Check if all dependencies are completed
                deps_met = all(
                    any(n.id == dep_id and n.status == "completed" for n in state.nodes)
                    for dep_id in node.depends_on
                )
                if deps_met:
                    node.status = "ready"
                    return node
        return None

    async def _execute_node(self, state: WorkflowState, node: WorkflowNode, auto_approve_hitl: bool = False) -> None:
        state.current_node_id = node.id
        node.status = "executing"
        node.started_at = datetime.utcnow()
        node.invocation_count += 1
        state.total_agent_invocations += 1
        await self.wf_repo.save_workflow(state)

        await self.emit_event(
            workflow_id=state.workflow_id,
            event_type="node_started",
            node_id=node.id,
            agent_id=node.agent_id,
            payload={"task_type": node.task_type, "invocation_count": node.invocation_count}
        )

        try:
            # Policy guardrail validation
            self.policy.validate_node_invocation(state, node)

            # Context injection from state and prior artifacts
            context = {
                "workflow_id": state.workflow_id,
                "workspace_id": state.workspace_id or "default_workspace",
                "conversation_id": state.workflow_id,
                "user_id": state.user_id or "default_user",
                "query": state.query,
                "artifacts": state.artifacts
            }

            # Execute via Deep Agent
            response = await self.deep_agent.execute_agent_task(
                agent_id=node.agent_id,
                task_type=node.task_type,
                input_data=node.input_data,
                context=context,
                workflow_id=state.workflow_id,
                node_id=node.id
            )

            # Store artifact if returned
            if response.artifact_name and response.result:
                artifact_content = response.result.get("artifact_content") or str(response.result)
                art_ref = await self.artifact_store.write_artifact(
                    workflow_id=state.workflow_id,
                    node_id=node.id,
                    agent_id=node.agent_id,
                    name=response.artifact_name,
                    content=artifact_content,
                    artifact_type=response.artifact_type or "markdown",
                    summary=response.artifact_summary
                )
                node.artifact_refs.append(art_ref.artifact_id)
                state.artifacts.append(art_ref)

                await self.emit_event(
                    workflow_id=state.workflow_id,
                    event_type="artifact_written",
                    node_id=node.id,
                    agent_id=node.agent_id,
                    payload={"artifact_id": art_ref.artifact_id, "name": art_ref.name, "summary": art_ref.summary}
                )

            node.output_data = response.result
            node.completed_at = datetime.utcnow()

            # Check next action: Dynamic Replan
            if response.next_action.type == "request_agent":
                logger.info(f"Node {node.id} requested dynamic replanning to agent {response.next_action.agent_id}")
                node.status = "completed"
                state = self.replanner.replan_on_feedback(state, node.id, response.next_action)
                await self.wf_repo.save_workflow(state)

                await self.emit_event(
                    workflow_id=state.workflow_id,
                    event_type="plan_updated",
                    node_id=node.id,
                    payload={
                        "plan_version": state.plan_version,
                        "replan_count": state.replan_count,
                        "reason": response.next_action.reason,
                        "nodes": [n.model_dump(mode="json") for n in state.nodes]
                    }
                )
                return

            # Check next action: Human In The Loop (HITL)
            if (response.next_action.type == "request_human" or node.hitl_required) and not auto_approve_hitl:
                node.status = "awaiting_approval"
                state.status = "awaiting_approval"
                pending_appr = HITLManager.create_pending_approval(
                    node=node,
                    reason=response.next_action.reason or "Human signoff required before proceeding.",
                    artifact_id=node.artifact_refs[0] if node.artifact_refs else None,
                    artifact_summary=response.artifact_summary,
                    proposed_output=response.result
                )
                state.pending_approval = pending_appr
                await self.wf_repo.save_workflow(state)

                await self.emit_event(
                    workflow_id=state.workflow_id,
                    event_type="interrupt_requested",
                    node_id=node.id,
                    agent_id=node.agent_id,
                    payload=pending_appr.model_dump(mode="json")
                )
                return

            # Completed successfully
            node.status = "completed"
            await self.wf_repo.save_workflow(state)

            await self.emit_event(
                workflow_id=state.workflow_id,
                event_type="node_completed",
                node_id=node.id,
                agent_id=node.agent_id,
                payload={"confidence": response.confidence, "output": response.result}
            )

        except Exception as e:
            logger.error(f"Node {node.id} execution failed: {e}")
            node.status = "failed"
            node.error_message = str(e)
            state.status = "failed"
            state.error_message = f"Node {node.id} failed: {str(e)}"
            await self.wf_repo.save_workflow(state)

            await self.emit_event(
                workflow_id=state.workflow_id,
                event_type="node_failed",
                node_id=node.id,
                agent_id=node.agent_id,
                payload={"error": str(e)}
            )

    async def resume_hitl(self, workflow_id: str, resolution: ApprovalResolution) -> WorkflowState:
        state = await self.wf_repo.get_workflow(workflow_id)
        if not state:
            raise WorkflowError(f"Workflow {workflow_id} not found.")

        state = HITLManager.apply_approval_decision(state, resolution)
        await self.wf_repo.save_workflow(state)

        await self.emit_event(
            workflow_id=workflow_id,
            event_type="hitl_resolved",
            payload={"decision": resolution.decision, "feedback": resolution.feedback}
        )

        if resolution.decision in ["approved", "edited"]:
            await self.execute_workflow_async(workflow_id)

        return state

    async def cancel_workflow(self, workflow_id: str, reason: str = "User cancelled") -> WorkflowState:
        state = await self.wf_repo.get_workflow(workflow_id)
        if not state:
            raise WorkflowError(f"Workflow {workflow_id} not found.")

        state = WorkflowCancellationHandler.cancel_workflow(state, reason)
        await self.wf_repo.save_workflow(state)

        await self.emit_event(
            workflow_id=workflow_id,
            event_type="workflow_cancelled",
            payload={"reason": reason}
        )

        return state


_orchestrator_instance: WorkflowOrchestrator | None = None


def get_workflow_orchestrator() -> WorkflowOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = WorkflowOrchestrator()
    return _orchestrator_instance
