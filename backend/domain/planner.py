import uuid
import re
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Protocol
from enum import IntEnum
from pydantic import BaseModel, Field
import httpx

from models.workflow import WorkflowState, WorkflowNode, WorkflowEdge
from models.agents import AgentDefinition
from services.agent_registry import AgentRegistry, get_agent_registry
from config.settings import get_settings

logger = logging.getLogger(__name__)


# ============================================================================
# Domain Models for Planning
# ============================================================================

class SDLCPhase(IntEnum):
    """Canonical SDLC sequence phases to guarantee sequence-proof dependencies."""
    REQUIREMENTS = 10     # Business Analyst
    ARCHITECTURE = 20     # Architect
    PRODUCT_OWNER = 30    # Product Owner
    DEVELOPMENT = 40      # Developer
    QUALITY_ENGINEERING = 50  # QE / Testing


class QuerySlice(BaseModel):
    """Represents a sliced semantic unit of user requirements."""
    slice_id: int
    text: str
    inferred_intent: str | None = None


class ClassifiedTaskIntent(BaseModel):
    """Result of classifying a query slice against agent capabilities in agents.json."""
    agent_id: str
    display_name: str
    task_type: str
    capability_matched: str
    phase: SDLCPhase
    confidence: float = 1.0
    task_prompt: str
    input_data: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# SOLID Interfaces (Protocols / Abstract Classes)
# ============================================================================

class IQuerySlicer(Protocol):
    """Single Responsibility: Slice/decompose natural language user request into requirement units."""
    def slice_query(self, query: str) -> list[QuerySlice]:
        ...


class IIntentClassifier(Protocol):
    """Single Responsibility: Classify requirement slices against agents.json capabilities."""
    def classify_intents(
        self,
        slices: list[QuerySlice],
        available_agents: list[AgentDefinition],
        original_query: str
    ) -> list[ClassifiedTaskIntent]:
        ...


class ISDLCSequenceEngine(Protocol):
    """Single Responsibility: Build a sequence-proof, topologically sorted DAG from classified intents."""
    def build_sdlc_graph(
        self,
        intents: list[ClassifiedTaskIntent],
        original_query: str,
        initial_context: dict[str, Any] | None = None
    ) -> tuple[list[WorkflowNode], list[WorkflowEdge]]:
        ...


# ============================================================================
# Concrete Implementations
# ============================================================================

class DeepAgentQuerySlicer:
    """Slices complex natural language queries using semantic boundaries and delimiters."""

    def slice_query(self, query: str) -> list[QuerySlice]:
        cleaned = query.strip()
        if not cleaned:
            return []

        # Split on commas, semicolons, numbered points, or transitional phrases ('and then', 'then', 'and')
        pattern = r"(?:\r?\n\s*\d+[\.\)]\s*|\r?\n\s*[-*]\s*|\s*;\s*|\s*,\s*and\s+|\s*,\s*then\s+|\s+and\s+then\s+|\s*,\s*|\s+then\s+)"
        parts = [p.strip() for p in re.split(pattern, cleaned, flags=re.IGNORECASE) if p.strip()]

        # Filter out trivial fragments (< 3 characters)
        meaningful_parts = [p for p in parts if len(p) >= 3]

        if not meaningful_parts:
            meaningful_parts = [cleaned]

        return [QuerySlice(slice_id=i + 1, text=part) for i, part in enumerate(meaningful_parts)]


class DeepAgentIntentClassifier:
    """Classifies sliced queries against agents in agents.json using LLM reasoning or capability matching."""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.settings = get_settings()

    def classify_intents(
        self,
        slices: list[QuerySlice],
        available_agents: list[AgentDefinition],
        original_query: str
    ) -> list[ClassifiedTaskIntent]:
        # Attempt LLM classification if Azure OpenAI / LLM credentials are configured
        if self._is_llm_configured():
            llm_result = self._classify_with_llm(slices, available_agents, original_query)
            if llm_result:
                return llm_result

        # Fallback to capability matching against agents.json
        return self._classify_with_capability_matcher(slices, available_agents, original_query)

    def _is_llm_configured(self) -> bool:
        return bool(
            self.settings.azure_openai_endpoint and
            self.settings.azure_openai_api_key and
            self.settings.azure_openai_deployment_name and
            self.settings.deep_agent_model_provider == "azure"
        )

    def _classify_with_llm(
        self,
        slices: list[QuerySlice],
        available_agents: list[AgentDefinition],
        original_query: str
    ) -> list[ClassifiedTaskIntent] | None:
        try:
            endpoint = self.settings.azure_openai_endpoint.rstrip("/")
            deployment = self.settings.azure_openai_deployment_name
            api_version = self.settings.azure_openai_api_version
            api_key = self.settings.azure_openai_api_key

            url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

            agent_manifest = [
                {
                    "agent_id": a.agent_id,
                    "display_name": a.display_name,
                    "capabilities": a.capabilities,
                    "supported_task_types": a.supported_task_types,
                    "purpose": a.purpose
                }
                for a in available_agents if a.status == "active"
            ]

            prompt = (
                f"You are the Deep Agent Planning Engine. Analyze this user workflow query and requirement slices:\n"
                f"Query: {original_query}\n"
                f"Slices: {[s.text for s in slices]}\n\n"
                f"Available Agents & Capabilities:\n{json.dumps(agent_manifest, indent=2)}\n\n"
                f"Map the request to an ordered SDLC plan. Return a JSON object with a list of 'tasks', each containing: "
                f"agent_id, task_type, capability_matched, task_prompt, and confidence."
            )

            headers = {
                "Content-Type": "application/json",
                "api-key": api_key
            }
            body = {
                "messages": [
                    {"role": "system", "content": "You are a professional SDLC multi-agent workflow planner. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }

            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, headers=headers, json=body)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    tasks = parsed.get("tasks", [])
                    results = []
                    for t in tasks:
                        agent = next((a for a in available_agents if a.agent_id == t.get("agent_id")), None)
                        if agent:
                            phase = self._get_phase_for_agent(agent.agent_id)
                            results.append(
                                ClassifiedTaskIntent(
                                    agent_id=agent.agent_id,
                                    display_name=agent.display_name,
                                    task_type=t.get("task_type") or agent.supported_task_types[0],
                                    capability_matched=t.get("capability_matched") or agent.capabilities[0],
                                    phase=phase,
                                    confidence=float(t.get("confidence", 0.95)),
                                    task_prompt=t.get("task_prompt", original_query),
                                    input_data={"prompt": t.get("task_prompt", original_query)}
                                )
                            )
                    if results:
                        return results
        except Exception as e:
            logger.warning(f"LLM planning inference fallback: {e}")
        return None

    def _classify_with_capability_matcher(
        self,
        slices: list[QuerySlice],
        available_agents: list[AgentDefinition],
        original_query: str
    ) -> list[ClassifiedTaskIntent]:
        """Matches slices and capabilities dynamically against agents.json."""
        intents_by_agent: dict[str, ClassifiedTaskIntent] = {}

        # Keywords mapped to registered agent capabilities in agents.json
        capability_keywords = {
            "business-analyst": ["brd", "requirement", "requirements", "business", "stories", "user story", "spec", "synopsis", "analyst"],
            "architect": ["architect", "architecture", "design", "c4", "diagram", "infra", "infrastructure", "api design", "nld", "component"],
            "product-owner": ["sprint", "backlog", "po", "product owner", "prioritize", "prioritization", "roadmap", "acceptance criteria"],
            "developer": ["implement", "code", "dev", "developer", "scaffold", "scaffolding", "microservice", "backend", "frontend", "tasks"],
            "qe": ["qa", "qe", "test", "testing", "quality", "strategy", "test strategy", "test cases", "automation", "verify", "verification"]
        }

        full_text = original_query.lower()

        for agent in available_agents:
            if agent.status != "active" or not agent.invocation_enabled:
                continue

            agent_id = agent.agent_id
            keywords = capability_keywords.get(agent_id, [agent_id])
            
            # Check if any slice matches or full query matches this agent's capabilities
            matched_slice_texts = []
            for s in slices:
                s_lower = s.text.lower()
                if any(kw in s_lower for kw in keywords) or any(cap.lower().replace("_", " ") in s_lower for cap in agent.capabilities):
                    matched_slice_texts.append(s.text)

            is_full_query_match = any(kw in full_text for kw in keywords)
            
            # If query mentions SDLC / end-to-end / platform, include standard core pipeline
            is_broad_request = any(term in full_text for term in ["platform", "system", "app", "application", "sdlc", "end to end", "pipeline", "workflow"])
            
            if matched_slice_texts or is_full_query_match or is_broad_request:
                # Determine task prompt and task type
                task_prompt = " ".join(matched_slice_texts) if matched_slice_texts else original_query
                task_type = self._pick_best_task_type(agent, task_prompt)
                capability = agent.capabilities[0] if agent.capabilities else "general_task"
                phase = self._get_phase_for_agent(agent_id)

                intents_by_agent[agent_id] = ClassifiedTaskIntent(
                    agent_id=agent_id,
                    display_name=agent.display_name,
                    task_type=task_type,
                    capability_matched=capability,
                    phase=phase,
                    confidence=0.95,
                    task_prompt=task_prompt,
                    input_data=self._build_input_data_for_agent(agent_id, task_prompt, original_query)
                )

        return list(intents_by_agent.values())

    def _get_phase_for_agent(self, agent_id: str) -> SDLCPhase:
        mapping = {
            "business-analyst": SDLCPhase.REQUIREMENTS,
            "architect": SDLCPhase.ARCHITECTURE,
            "product-owner": SDLCPhase.PRODUCT_OWNER,
            "developer": SDLCPhase.DEVELOPMENT,
            "qe": SDLCPhase.QUALITY_ENGINEERING,
        }
        return mapping.get(agent_id, SDLCPhase.DEVELOPMENT)

    def _pick_best_task_type(self, agent: AgentDefinition, prompt: str) -> str:
        p_lower = prompt.lower()
        if agent.agent_id == "business-analyst":
            if "story" in p_lower or "stories" in p_lower:
                return "create_user_stories"
            return "dynamic_workflow_ba_task"
        elif agent.agent_id == "architect":
            if "nld" in p_lower:
                return "update_design_nld"
            if "mermaid" in p_lower:
                return "render_mermaid"
            return "send_message"
        elif agent.agent_id == "developer":
            return "handle_dev_message"
        elif agent.agent_id == "product-owner":
            if "prioritize" in p_lower:
                return "prioritize_backlog"
            return "sprint_planning"
        elif agent.agent_id == "qe":
            if "case" in p_lower:
                return "generate_test_cases"
            return "generate_test_strategy"
        return agent.supported_task_types[0] if agent.supported_task_types else "task"

    def _build_input_data_for_agent(self, agent_id: str, prompt: str, original_query: str) -> dict[str, Any]:
        if agent_id == "business-analyst":
            return {"prompt": prompt or original_query}
        elif agent_id == "architect":
            return {"user_message": f"Design architecture for: {prompt or original_query}"}
        elif agent_id == "developer":
            return {"message": f"Implement services for: {prompt or original_query}"}
        elif agent_id == "product-owner":
            return {"prompt": f"Sprint planning for: {prompt or original_query}"}
        elif agent_id == "qe":
            return {"requirements": prompt or original_query}
        return {"prompt": prompt}


class SDLCSequenceEngine:
    """Builds a sequence-proof, topologically sorted DAG strictly obeying SDLC phases and dependencies."""

    def build_sdlc_graph(
        self,
        intents: list[ClassifiedTaskIntent],
        original_query: str,
        initial_context: dict[str, Any] | None = None
    ) -> tuple[list[WorkflowNode], list[WorkflowEdge]]:
        initial_context = initial_context or {}

        # 1. Sort intents by SDLCPhase to guarantee sequence proofing
        sorted_intents = sorted(intents, key=lambda item: int(item.phase))

        nodes: list[WorkflowNode] = []
        edges: list[WorkflowEdge] = []

        prev_node_id: str | None = None

        for idx, intent in enumerate(sorted_intents, start=1):
            node_id = f"node-{idx}-{intent.agent_id.replace('_', '-')}"
            display_title = f"{idx}. {self._get_phase_title(intent.phase)} ({intent.agent_id.title()})"

            input_payload = {**intent.input_data, **initial_context}

            node = WorkflowNode(
                id=node_id,
                agent_id=intent.agent_id,
                task_type=intent.task_type,
                display_name=display_title,
                input_data=input_payload,
                status="ready" if idx == 1 else "planned",
                plan_version=1,
                depends_on=[prev_node_id] if prev_node_id else [],
                hitl_required=False,
                position_x=50.0 + ((idx - 1) * 280.0),
                position_y=100.0
            )
            nodes.append(node)

            if prev_node_id:
                edges.append(
                    WorkflowEdge(
                        id=f"edge-{prev_node_id}-{node_id}",
                        source=prev_node_id,
                        target=node_id,
                        plan_version=1
                    )
                )

            prev_node_id = node_id

        return nodes, edges

    def _get_phase_title(self, phase: SDLCPhase) -> str:
        titles = {
            SDLCPhase.REQUIREMENTS: "Business Requirements Analysis",
            SDLCPhase.ARCHITECTURE: "System Architecture Design",
            SDLCPhase.PRODUCT_OWNER: "Sprint Planning & Backlog",
            SDLCPhase.DEVELOPMENT: "Microservice Implementation",
            SDLCPhase.QUALITY_ENGINEERING: "Quality Strategy & Test Suite",
        }
        return titles.get(phase, "Task Execution")


# ============================================================================
# Main Workflow Planner (Dependency Inversion / Coordinator)
# ============================================================================

class WorkflowPlanner:
    """
    SOLID-compliant Multi-Agent Workflow Planning Coordinator.
    Decomposes queries, classifies intents against agents.json capabilities,
    and generates sequence-proof SDLC workflow states.
    """

    def __init__(
        self,
        registry: AgentRegistry | None = None,
        slicer: IQuerySlicer | None = None,
        classifier: IIntentClassifier | None = None,
        sequence_engine: ISDLCSequenceEngine | None = None
    ):
        self.registry = registry or get_agent_registry()
        self.slicer = slicer or DeepAgentQuerySlicer()
        self.classifier = classifier or DeepAgentIntentClassifier(self.registry)
        self.sequence_engine = sequence_engine or SDLCSequenceEngine()

    def generate_initial_plan(
        self,
        query: str,
        workspace_id: str = "default_workspace",
        user_id: str = "default_user",
        initial_context: dict[str, Any] | None = None
    ) -> WorkflowState:
        workflow_id = f"wf-{uuid.uuid4().hex[:8]}"
        initial_context = initial_context or {}

        # 1. Slicing: Decompose user query into discrete functional requirement slices
        slices = self.slicer.slice_query(query)
        logger.info(f"Query decomposed into {len(slices)} slices for workflow {workflow_id}")

        # 2. Intent Classification & Capability Matching: Match slices against agents.json
        available_agents = self.registry.list_agents()
        intents = self.classifier.classify_intents(slices, available_agents, query)
        logger.info(f"Classified {len(intents)} agent task intents matching agents.json capabilities")

        # 3. SDLC Sequence Proofing: Construct topological DAG
        nodes, edges = self.sequence_engine.build_sdlc_graph(intents, query, initial_context)

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
