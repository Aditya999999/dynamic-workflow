import pytest
from domain.planner import WorkflowPlanner
from domain.replanner import WorkflowReplanner
from models.workflow import NextAction


def test_dynamic_replanner():
    planner = WorkflowPlanner()
    replanner = WorkflowReplanner()

    state = planner.generate_initial_plan(query="Design payment gateway")
    initial_version = state.plan_version
    initial_node_count = len(state.nodes)

    arch_node = next(n for n in state.nodes if n.agent_id == "architect")

    next_action = NextAction(
        type="request_agent",
        agent_id="business-analyst",
        task_type="dynamic_workflow_ba_task",
        reason="Clarification needed on multi-currency settlement window"
    )

    updated_state = replanner.replan_on_feedback(state, arch_node.id, next_action)

    assert updated_state.plan_version == initial_version + 1
    assert updated_state.replan_count == 1
    assert len(updated_state.nodes) == initial_node_count + 2
    assert any("Clarification (Business-Analyst)" in n.display_name for n in updated_state.nodes)
