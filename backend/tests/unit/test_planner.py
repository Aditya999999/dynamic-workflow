import pytest
from domain.planner import WorkflowPlanner


def test_initial_plan_generation():
    planner = WorkflowPlanner()
    state = planner.generate_initial_plan(
        query="Create a BRD for an online payment platform, design the architecture, prepare implementation tasks, and create a QA strategy."
    )

    assert state.plan_version == 1
    assert state.status == "planned"
    assert len(state.nodes) >= 4

    agent_sequence = [n.agent_id for n in state.nodes]
    assert agent_sequence[0] == "business-analyst"
    assert agent_sequence[1] == "architect"
    assert "developer" in agent_sequence
    assert "qe" in agent_sequence
