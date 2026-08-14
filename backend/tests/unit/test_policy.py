import pytest
from models.workflow import WorkflowState, WorkflowNode, WorkflowEdge
from models.errors import PolicyViolationError
from domain.orchestration_policy import OrchestrationPolicy


def test_detect_cycle():
    policy = OrchestrationPolicy()
    state = WorkflowState(
        workflow_id="wf-test",
        query="test",
        nodes=[
            WorkflowNode(id="n1", agent_id="business-analyst", task_type="dynamic_workflow_ba_task", display_name="N1"),
            WorkflowNode(id="n2", agent_id="architect", task_type="send_message", display_name="N2"),
        ],
        edges=[
            WorkflowEdge(id="e1", source="n1", target="n2"),
            WorkflowEdge(id="e2", source="n2", target="n1"),
        ]
    )
    assert policy.detect_cycle(state) is True


def test_replan_limit_guardrail():
    policy = OrchestrationPolicy()
    state = WorkflowState(
        workflow_id="wf-test",
        query="test",
        replan_count=7,
        nodes=[]
    )
    with pytest.raises(PolicyViolationError) as exc:
        policy.validate_workflow_limits(state)
    assert "replan limit" in str(exc.value.message).lower()
