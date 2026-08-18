import pytest
from domain.planner import (
    WorkflowPlanner,
    DeepAgentQuerySlicer,
    DeepAgentIntentClassifier,
    DeepAgentScopeValidator,
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
    parsed_req = slicer.parse_user_request(query)
    slices = slicer.slice_query(query)
    agents = registry.list_agents()

    intents = classifier.classify_intents(parsed_req, slices, agents, query)
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


def test_scenario_1_out_of_scope_rejection():
    planner = WorkflowPlanner()
    
    # Non-SDLC queries: trivia, chit-chat, jokes
    out_of_scope_queries = [
        "What is the capital of France?",
        "tell me a joke",
        "hi",
        "who is the president of USA"
    ]
    
    for q in out_of_scope_queries:
        state = planner.generate_initial_plan(query=q)
        assert state.status == "failed"
        assert len(state.nodes) == 0
        assert len(state.edges) == 0
        assert state.error_message is not None
        assert "outside the scope of Software Development Life Cycle (SDLC) workflows" in state.error_message


def test_scenario_2_legitimate_nlq_multi_agent():
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


def test_scenario_3_pasted_tsd_with_developer_action_only():
    planner = WorkflowPlanner()
    
    tsd_content = """develop code for this TSD:
# Technical Specification Document (TSD)
## Module 1: Authentication Service
Requirements:
- User registration and login using JWT tokens
- Password hashing with bcrypt
- System Architecture design specification with C4 diagram
- Quality assurance and test strategy guidelines
- Sprint backlog story points and sprint planning acceptance criteria
"""

    state = planner.generate_initial_plan(query=tsd_content)

    assert state.status == "planned"
    # Even though the pasted TSD mentions "Architecture", "Quality assurance", "BRD", "Sprint backlog",
    # ONLY the developer agent should be selected because the user's action command is "develop code for this TSD"
    assert len(state.nodes) == 1
    assert state.nodes[0].agent_id == "developer"
    assert state.nodes[0].status == "ready"
    
    # Verify that the full TSD document payload was preserved in input_data for the developer
    input_message = state.nodes[0].input_data.get("message") or state.nodes[0].input_data.get("prompt")
    assert "Technical Specification Document" in input_message
    assert "Authentication Service" in input_message


def test_scenario_3_pasted_architecture_with_qe_test_action_only():
    planner = WorkflowPlanner()
    
    query = """Please generate test strategy and test cases based on the below architecture document:
# Microservice Architecture Document
Component 1: Payment Gateway API
Component 2: Kafka Event Stream
Component 3: PostgreSQL Database
"""

    state = planner.generate_initial_plan(query=query)

    assert state.status == "planned"
    assert len(state.nodes) == 1
    assert state.nodes[0].agent_id == "qe"
    assert state.nodes[0].status == "ready"
    
    input_reqs = state.nodes[0].input_data.get("requirements") or state.nodes[0].input_data.get("prompt")
    assert "Microservice Architecture Document" in input_reqs
