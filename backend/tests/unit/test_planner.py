import pytest
from domain.planner import (
    WorkflowPlanner,
    DeepAgentQuerySlicer,
    DeepAgentIntentClassifier,
    SDLCSequenceEngine,
    QuerySlice,
    ClassifiedTaskIntent,
    SDLCPhase
)
from services.agent_registry import get_agent_registry


def test_query_slicer_decomposition():
    slicer = DeepAgentQuerySlicer()
    query = "Create a BRD for an online payment platform, design the architecture, prepare implementation tasks, and create a QA strategy."
    slices = slicer.slice_query(query)

    assert len(slices) >= 4
    slice_texts = [s.text.lower() for s in slices]
    assert any("brd" in t for t in slice_texts)
    assert any("architecture" in t for t in slice_texts)
    assert any("tasks" in t or "implementation" in t for t in slice_texts)
    assert any("qa" in t or "strategy" in t for t in slice_texts)


def test_intent_classifier_against_agent_registry():
    registry = get_agent_registry()
    classifier = DeepAgentIntentClassifier(registry)
    slicer = DeepAgentQuerySlicer()

    query = "Create user stories for checkout flow and write test cases"
    slices = slicer.slice_query(query)
    agents = registry.list_agents()

    intents = classifier.classify_intents(slices, agents, query)
    agent_ids = [intent.agent_id for intent in intents]

    assert "business-analyst" in agent_ids
    assert "qe" in agent_ids


def test_sdlc_sequence_engine_phase_ordering():
    engine = SDLCSequenceEngine()
    
    # Intentionally provided out of order: QE first, then Developer, then BA
    unordered_intents = [
        ClassifiedTaskIntent(
            agent_id="qe",
            display_name="Quality Engineer Agent",
            task_type="generate_test_strategy",
            capability_matched="test_strategy",
            phase=SDLCPhase.QUALITY_ENGINEERING,
            task_prompt="QE prompt"
        ),
        ClassifiedTaskIntent(
            agent_id="developer",
            display_name="Developer Agent",
            task_type="handle_dev_message",
            capability_matched="code_generation",
            phase=SDLCPhase.DEVELOPMENT,
            task_prompt="Dev prompt"
        ),
        ClassifiedTaskIntent(
            agent_id="business-analyst",
            display_name="Business Analyst Agent",
            task_type="dynamic_workflow_ba_task",
            capability_matched="brd_generation",
            phase=SDLCPhase.REQUIREMENTS,
            task_prompt="BA prompt"
        )
    ]

    nodes, edges = engine.build_sdlc_graph(unordered_intents, "Test query")

    # Verify nodes are sorted strictly according to SDLC sequence
    assert len(nodes) == 3
    assert nodes[0].agent_id == "business-analyst"
    assert nodes[1].agent_id == "developer"
    assert nodes[2].agent_id == "qe"

    # Verify dependency chain
    assert nodes[0].depends_on == []
    assert nodes[1].depends_on == [nodes[0].id]
    assert nodes[2].depends_on == [nodes[1].id]

    assert len(edges) == 2
    assert edges[0].source == nodes[0].id
    assert edges[0].target == nodes[1].id
    assert edges[1].source == nodes[1].id
    assert edges[1].target == nodes[2].id


def test_initial_plan_generation_end_to_end():
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

    # Verify first node is ready and others are planned
    assert state.nodes[0].status == "ready"
    assert all(n.status == "planned" for n in state.nodes[1:])
