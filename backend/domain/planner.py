import uuid
import re
import json
import logging
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


class ParsedUserRequest(BaseModel):
    """Represents the decomposed user input separating action commands from pasted document content."""
    action_prompt: str
    document_payload: str | None = None
    has_pasted_doc: bool = False
    is_sdlc_scoped: bool = True
    unscoped_reason: str | None = None


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
# Scope Validator (Scenario 1: Non-SDLC Filter)
# ============================================================================

class IQueryScopeValidator(Protocol):
    """Single Responsibility: Determine if a user query is in-scope for SDLC workflows."""
    def validate_scope(self, query: str) -> tuple[bool, str | None]:
        ...


class DeepAgentScopeValidator:
    """Validates user queries against SDLC domain boundaries and filters out irrelevant chit-chat/trivia."""

    SDLC_KEYWORDS = {
        # Requirements / BA
        "brd", "requirement", "requirements", "user story", "user stories", "spec", "specification",
        "prd", "synopsis", "acceptance criteria", "business analyst", "use case", "use cases",
        # Architecture / Design
        "design", "architect", "architecture", "c4", "diagram", "diagrams", "system design", "nld", "infrastructure",
        "api design", "database design", "db schema", "microservice", "microservices", "component", "gateway",
        # Development / Code
        "code", "develop", "developer", "development", "implement", "implementation", "scaffold", "scaffolding",
        "fastapi", "backend", "frontend", "api", "endpoint", "endpoints", "service", "services", "server", "client",
        "controller", "repository", "function", "class", "algorithm", "refactor", "bug", "fix", "payment",
        "python", "typescript", "javascript", "java", "golang", "c#", "react", "angular", "vue", "build", "create",
        # Product Owner / Agile
        "product owner", "po", "sprint", "sprint planning", "backlog", "prioritize", "prioritization",
        "roadmap", "epic", "epics", "milestone", "story points",
        # Quality Engineering / QE / QA
        "qe", "qa", "test", "testing", "test strategy", "test cases", "unit test", "unit tests",
        "integration test", "integration tests", "automation", "coverage", "verify", "verification",
        "pytest", "jest", "postman", "e2e test", "load testing", "security test",
        # General Software Engineering & Platforms
        "software", "app", "application", "platform", "system", "feature", "pipeline", "ci/cd",
        "workflow", "tsd", "technical specification", "rest api", "graphql", "crud", "auth", "authentication"
    }

    OUT_OF_SCOPE_PATTERNS = [
        r"^(hi|hello|hey|greetings|good morning|good evening|good afternoon)[\s!.]*$",
        r"^(who are you|what is your name|what can you do|how are you|tell me about yourself)[\s?.]*$",
        r"^what is the (capital|weather|distance|president|population|currency) of\b",
        r"^(tell me a joke|tell me a story|sing a song|write a poem)\b",
        r"^calculate\s+\d+[\s\d\+\-\*\/\^\%]*$",
        r"^(how to cook|recipe for|bake a cake|make coffee)\b",
        r"^(who won|score of|match between|football|cricket|nba|movie|actor|song)\b"
    ]

    def validate_scope(self, query: str) -> tuple[bool, str | None]:
        cleaned = query.strip()
        if not cleaned:
            return False, "Query is empty."

        cleaned_lower = cleaned.lower()

        # Check explicit out-of-scope regex patterns
        for pattern in self.OUT_OF_SCOPE_PATTERNS:
            if re.search(pattern, cleaned_lower):
                return False, (
                    "Your request appears to be outside the scope of Software Development Life Cycle (SDLC) workflows. "
                    "The Dynamic Workflow Orchestrator handles SDLC tasks such as Requirements Analysis (BRD), "
                    "Architecture Design, Sprint Planning, Microservice Development, and QA/Test Strategy. "
                    "Please provide a software engineering requirement or task."
                )

        # Check if any SDLC keyword or pattern matches
        has_sdlc_keyword = any(kw in cleaned_lower for kw in self.SDLC_KEYWORDS)
        
        # Check code / markdown / structural indicators
        has_code_block = "```" in cleaned or "def " in cleaned or "class " in cleaned or "import " in cleaned
        has_doc_structure = any(header in cleaned for header in ["#", "##", "---", "###", "Overview:", "Requirements:", "API:"])

        if has_sdlc_keyword or has_code_block or has_doc_structure:
            return True, None

        # If query is purely conversational or non-technical words without SDLC relevance
        words = re.findall(r"\b\w+\b", cleaned_lower)
        if len(words) <= 5 and not has_sdlc_keyword:
            return False, (
                "Your request appears to be outside the scope of Software Development Life Cycle (SDLC) workflows. "
                "Please provide a software engineering requirement (e.g., 'Create BRD and Architecture for an online payment service', "
                "'Develop code for this TSD', or 'Generate test strategy')."
            )

        return True, None


# ============================================================================
# SOLID Interfaces (Protocols / Abstract Classes)
# ============================================================================

class IQuerySlicer(Protocol):
    """Single Responsibility: Slice/decompose natural language user request and separate pasted documents."""
    def parse_user_request(self, query: str) -> ParsedUserRequest:
        ...
    def slice_query(self, query: str) -> list[QuerySlice]:
        ...


class IIntentClassifier(Protocol):
    """Single Responsibility: Classify requirement slices against agents.json capabilities."""
    def classify_intents(
        self,
        parsed_request: ParsedUserRequest,
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
    """
    Slices natural language queries using semantic boundaries and separates
    user action commands from pasted technical documents (TSD / BRD / Code).
    """

    ACTION_VERB_PATTERNS = [
        r"\b(?:develop|code|implement|generate|create|write|build|scaffold|design|review|test|prioritize|analyze|prepare)\b"
    ]

    DOC_INDICATORS = [
        "tsd", "technical specification", "architecture document", "brd", "business requirements",
        "api specification", "database schema", "openapi", "swagger", "system design"
    ]

    def parse_user_request(self, query: str) -> ParsedUserRequest:
        cleaned = query.strip()
        if not cleaned:
            return ParsedUserRequest(action_prompt="", has_pasted_doc=False, is_sdlc_scoped=False)

        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]

        # Check if this is a Pasted Document + Action Request (Scenario 3)
        # Indicators: multiple lines, long length (>150 chars), markdown headers, code blocks, or explicit TSD markers
        is_multiline = len(lines) >= 3
        is_long = len(cleaned) >= 150
        has_doc_syntax = "```" in cleaned or any(line.startswith(("#", "##", "---", "###")) for line in lines)
        has_doc_mention = any(doc_ind in cleaned.lower() for doc_ind in self.DOC_INDICATORS)

        if (is_multiline and (is_long or has_doc_syntax or has_doc_mention)):
            # Check Pattern A: Action command is at the top lines (1st or 2nd line)
            first_line = lines[0]
            first_line_lower = first_line.lower()
            if any(re.search(pat, first_line_lower) for pat in self.ACTION_VERB_PATTERNS) and (
                any(doc_ind in first_line_lower for doc_ind in self.DOC_INDICATORS)
                or any(ref in first_line_lower for ref in ["this", "the following", "below", "attached", "provided", "given"])
                or len(lines) >= 4
            ):
                action_prompt = self._clean_action_prompt(first_line.rstrip(":\n\r "))
                doc_payload = "\n".join(lines[1:])
                return ParsedUserRequest(
                    action_prompt=action_prompt,
                    document_payload=doc_payload,
                    has_pasted_doc=True,
                    is_sdlc_scoped=True
                )

            # Check Pattern B: Action command is at the bottom line
            last_line = lines[-1]
            last_line_lower = last_line.lower()
            if any(re.search(pat, last_line_lower) for pat in self.ACTION_VERB_PATTERNS) and (
                any(doc_ind in last_line_lower for doc_ind in self.DOC_INDICATORS)
                or any(ref in last_line_lower for ref in ["above", "this", "the above", "given", "provided"])
            ):
                action_prompt = self._clean_action_prompt(last_line.rstrip(":\n\r "))
                doc_payload = "\n".join(lines[:-1])
                return ParsedUserRequest(
                    action_prompt=action_prompt,
                    document_payload=doc_payload,
                    has_pasted_doc=True,
                    is_sdlc_scoped=True
                )

            # Check Pattern C: Markdown / Document starting with title, action mentioned in query
            action_match = re.search(
                r"(?:please\s+)?(develop|code|implement|generate|create|write|build|design|test|prioritize)\s+[^.\n\r]+",
                cleaned,
                flags=re.IGNORECASE
            )
            if action_match:
                action_prompt = self._clean_action_prompt(action_match.group(0).strip())
                return ParsedUserRequest(
                    action_prompt=action_prompt,
                    document_payload=cleaned,
                    has_pasted_doc=True,
                    is_sdlc_scoped=True
                )

        # Standard NLQ (Scenario 2)
        return ParsedUserRequest(
            action_prompt=cleaned,
            document_payload=None,
            has_pasted_doc=False,
            is_sdlc_scoped=True
        )

    def _clean_action_prompt(self, raw_action: str) -> str:
        """Strips out reference phrases like 'based on the below architecture document' from the action command."""
        cleaned = re.sub(
            r"\s*(?:based on|from|for|using|referencing|in)\s+(?:the\s+)?(?:below|above|following|this|attached|provided|given)?\s*.*",
            "",
            raw_action,
            flags=re.IGNORECASE
        ).strip()
        return cleaned if len(cleaned) >= 4 else raw_action

    def slice_query(self, query: str) -> list[QuerySlice]:
        cleaned = query.strip()
        if not cleaned:
            return []

        pattern = r"(?:\r?\n\s*\d+[\.\)]\s*|\r?\n\s*[-*]\s*|\s*;\s*|\s*,\s*and\s+|\s*,\s*then\s+|\s+and\s+then\s+|\s*,\s*|\s+then\s+)"
        parts = [p.strip() for p in re.split(pattern, cleaned, flags=re.IGNORECASE) if p.strip()]
        meaningful_parts = [p for p in parts if len(p) >= 3]

        if not meaningful_parts:
            meaningful_parts = [cleaned]

        return [QuerySlice(slice_id=i + 1, text=part) for i, part in enumerate(meaningful_parts)]


class DeepAgentIntentClassifier:
    """Classifies queries against agents.json capabilities with action isolation for pasted documents and scope guardrails."""

    def __init__(self, registry: AgentRegistry, scope_validator: IQueryScopeValidator | None = None):
        self.registry = registry
        self.settings = get_settings()
        self.scope_validator = scope_validator or DeepAgentScopeValidator()

    def classify_intents(
        self,
        parsed_request: ParsedUserRequest,
        slices: list[QuerySlice],
        available_agents: list[AgentDefinition],
        original_query: str
    ) -> list[ClassifiedTaskIntent]:
        # 1. Validate SDLC scope (Scenario 1: Non-SDLC rejection)
        is_scoped, unscoped_reason = self.scope_validator.validate_scope(parsed_request.action_prompt or original_query)
        if not is_scoped:
            logger.info(f"Query flagged as out-of-scope for SDLC: {unscoped_reason}")
            return []

        # 2. Attempt LLM classification if Azure OpenAI credentials are configured
        if self._is_llm_configured():
            llm_result = self._classify_with_llm(parsed_request, slices, available_agents, original_query)
            if llm_result:
                return self._consolidate_intents_per_agent(llm_result)

        # 3. Fallback to capability matching against agents.json
        matched_intents = self._classify_with_capability_matcher(parsed_request, slices, available_agents, original_query)
        return self._consolidate_intents_per_agent(matched_intents)

    def _is_llm_configured(self) -> bool:
        return bool(
            self.settings.azure_openai_endpoint and
            self.settings.azure_openai_api_key and
            self.settings.azure_openai_deployment_name and
            self.settings.deep_agent_model_provider == "azure"
        )

    def _consolidate_intents_per_agent(self, intents: list[ClassifiedTaskIntent]) -> list[ClassifiedTaskIntent]:
        """Consolidates multiple intents per agent into a single canonical stage to prevent duplicate nodes."""
        consolidated: dict[str, ClassifiedTaskIntent] = {}
        for item in intents:
            if item.agent_id not in consolidated:
                consolidated[item.agent_id] = item
            else:
                existing = consolidated[item.agent_id]
                existing.task_prompt = f"{existing.task_prompt}; {item.task_prompt}"
        return list(consolidated.values())

    def _classify_with_llm(
        self,
        parsed_request: ParsedUserRequest,
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
                f"You are the Deep Agent SDLC Planning Engine. Analyze the user workflow query:\n"
                f"Full Query: {original_query[:2000]}\n"
                f"Action Command: {parsed_request.action_prompt}\n"
                f"Has Attached Document: {parsed_request.has_pasted_doc}\n"
                f"Slices: {[s.text for s in slices]}\n\n"
                f"Available Agents & Capabilities in agents.json:\n{json.dumps(agent_manifest, indent=2)}\n\n"
                f"Rules:\n"
                f"1. If the query is NOT related to software development lifecycle (e.g. general chit-chat, trivia, weather), return a JSON object with 'is_sdlc_scoped': false, 'tasks': [].\n"
                f"2. If the user provided a pasted document (e.g., TSD, BRD) and asked for a specific action (e.g., 'develop code for this TSD'), ONLY select the agent(s) required for that specific action (e.g. developer only). DO NOT select other agents whose keywords happen to appear inside the document text.\n"
                f"3. If the user asked a full-spectrum requirement (e.g., 'Build an e-commerce platform'), select relevant agents in SDLC order.\n\n"
                f"Return a JSON object with: 'is_sdlc_scoped': true/false, 'tasks': list of objects each containing 'agent_id', 'task_type', 'capability_matched', 'task_prompt', and 'confidence'."
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
                    if parsed.get("is_sdlc_scoped") is False:
                        return []
                    tasks = parsed.get("tasks", [])
                    results = []
                    for t in tasks:
                        agent = next((a for a in available_agents if a.agent_id == t.get("agent_id")), None)
                        if agent:
                            phase = self._get_phase_for_agent(agent.agent_id)
                            task_prompt = t.get("task_prompt", parsed_request.action_prompt or original_query)
                            results.append(
                                ClassifiedTaskIntent(
                                    agent_id=agent.agent_id,
                                    display_name=agent.display_name,
                                    task_type=t.get("task_type") or agent.supported_task_types[0],
                                    capability_matched=t.get("capability_matched") or agent.capabilities[0],
                                    phase=phase,
                                    confidence=float(t.get("confidence", 0.95)),
                                    task_prompt=task_prompt,
                                    input_data=self._build_input_data_for_agent(
                                        agent.agent_id,
                                        task_prompt,
                                        original_query,
                                        parsed_request.document_payload
                                    )
                                )
                            )
                    if results:
                        return results
        except Exception as e:
            logger.warning(f"LLM planning inference fallback: {e}")
        return None

    def _classify_with_capability_matcher(
        self,
        parsed_request: ParsedUserRequest,
        slices: list[QuerySlice],
        available_agents: list[AgentDefinition],
        original_query: str
    ) -> list[ClassifiedTaskIntent]:
        """
        Matches agent capabilities against user requirements.
        If a pasted document is present (Scenario 3), capability matching is performed STRICTLY on the action prompt.
        """
        intents_by_agent: dict[str, ClassifiedTaskIntent] = {}

        capability_keywords = {
            "business-analyst": ["brd", "requirement", "requirements", "user story", "user stories", "synopsis", "analyst", "create user stories"],
            "architect": ["architect", "architecture", "design", "c4", "diagram", "diagrams", "infrastructure", "api design", "nld", "component"],
            "product-owner": ["sprint", "backlog", "po", "product owner", "prioritize", "prioritization", "roadmap", "acceptance criteria"],
            "developer": ["develop", "code", "dev", "developer", "implement", "implementation", "scaffold", "scaffolding", "microservice", "backend", "frontend", "tasks", "service"],
            "qe": ["qa", "qe", "test", "testing", "test strategy", "test cases", "quality", "automation", "verify", "verification", "unit test"]
        }

        # If a pasted document was detected, focus matching ONLY on the user's action command
        if parsed_request.has_pasted_doc:
            # Strip out trailing document references like 'based on the below architecture document' or 'for this TSD'
            clean_action = re.sub(
                r"\s*(?:based on|from|for|using|referencing|in)\s+(?:the\s+)?(?:below|above|following|this|attached|provided|given)?\s*.*",
                "",
                parsed_request.action_prompt,
                flags=re.IGNORECASE
            ).strip()
            target_text = (clean_action or parsed_request.action_prompt).lower()
            target_slices = self._filter_slices_for_action(slices, target_text)
        else:
            target_text = original_query.lower()
            target_slices = slices

        # Check if action explicitly specifies agents/tasks
        is_broad_request = (not parsed_request.has_pasted_doc) and any(
            term in target_text for term in ["platform", "system", "app", "application", "sdlc", "end to end", "pipeline", "full workflow", "complete workflow"]
        )

        for agent in available_agents:
            if agent.status != "active" or not agent.invocation_enabled:
                continue

            agent_id = agent.agent_id
            keywords = capability_keywords.get(agent_id, [agent_id])

            matched_slice_texts = []
            for s in target_slices:
                s_lower = s.text.lower()
                if any(kw in s_lower for kw in keywords) or any(cap.lower().replace("_", " ") in s_lower for cap in agent.capabilities):
                    matched_slice_texts.append(s.text)

            is_action_match = any(kw in target_text for kw in keywords)

            if matched_slice_texts or is_action_match or is_broad_request:
                task_prompt = " ".join(matched_slice_texts) if matched_slice_texts else (parsed_request.action_prompt or original_query)
                task_type = self._pick_best_task_type(agent, target_text)
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
                    input_data=self._build_input_data_for_agent(
                        agent_id,
                        task_prompt,
                        original_query,
                        parsed_request.document_payload
                    )
                )

        return list(intents_by_agent.values())

    def _filter_slices_for_action(self, slices: list[QuerySlice], clean_action_text: str) -> list[QuerySlice]:
        """Filters slices to only those that represent the user's clean action command, omitting the document body."""
        action_lower = clean_action_text.lower()
        matching_slices = [s for s in slices if s.text.lower() in action_lower or action_lower in s.text.lower()]
        return matching_slices if matching_slices else [QuerySlice(slice_id=1, text=clean_action_text)]

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
            if "case" in p_lower or "cases" in p_lower:
                return "generate_test_cases"
            return "generate_test_strategy"
        return agent.supported_task_types[0] if agent.supported_task_types else "task"

    def _build_input_data_for_agent(
        self,
        agent_id: str,
        prompt: str,
        original_query: str,
        document_payload: str | None = None
    ) -> dict[str, Any]:
        # If document payload was pasted, deliver the full document with the action prompt
        effective_payload = f"{prompt}\n\nTechnical Document / Context:\n{document_payload}" if document_payload else (prompt or original_query)

        if agent_id == "business-analyst":
            return {"prompt": effective_payload}
        elif agent_id == "architect":
            return {"user_message": f"Design architecture for: {effective_payload}"}
        elif agent_id == "developer":
            return {"message": f"Implement services for: {effective_payload}"}
        elif agent_id == "product-owner":
            return {"prompt": f"Sprint planning for: {effective_payload}"}
        elif agent_id == "qe":
            return {"requirements": effective_payload}
        return {"prompt": effective_payload}


class SDLCSequenceEngine:
    """Builds a sequence-proof, topologically sorted DAG strictly obeying SDLC phases and dependencies."""

    def build_sdlc_graph(
        self,
        intents: list[ClassifiedTaskIntent],
        original_query: str,
        initial_context: dict[str, Any] | None = None
    ) -> tuple[list[WorkflowNode], list[WorkflowEdge]]:
        initial_context = initial_context or {}

        # 1. Sort intents strictly by SDLCPhase to guarantee sequence proofing
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
                position_x=50.0 + ((idx - 1) * 300.0),
                position_y=120.0
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
    Handles all 3 operational scenarios:
    1. Irrelevant / Non-SDLC queries -> Handled with a helpful custom rejection message, blocking execution.
    2. Legitimate Natural Language SDLC requirements -> Smooth multi-stage DAG generation.
    3. Pasted Technical Documents + Action requests -> Action-isolated capability matching with payload preservation.
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

        # 1. Parse user input: Separate action command from any pasted technical document content
        parsed_request = self.slicer.parse_user_request(query)
        slices = self.slicer.slice_query(parsed_request.action_prompt if parsed_request.has_pasted_doc else query)
        logger.info(
            f"Parsed request for workflow {workflow_id}: has_pasted_doc={parsed_request.has_pasted_doc}, "
            f"action_prompt='{parsed_request.action_prompt[:60]}...', slices={len(slices)}"
        )

        # 2. Intent Classification & Capability Matching against agents.json
        available_agents = self.registry.list_agents()
        intents = self.classifier.classify_intents(parsed_request, slices, available_agents, query)

        # Scenario 1: Non-SDLC or Out-of-Scope query rejection
        if not intents:
            logger.warning(f"Workflow {workflow_id} aborted: Query '{query[:50]}' is out-of-scope for SDLC.")
            return WorkflowState(
                workflow_id=workflow_id,
                workspace_id=workspace_id,
                user_id=user_id,
                query=query,
                status="failed",
                plan_version=0,
                nodes=[],
                edges=[],
                current_node_id=None,
                artifacts=[],
                replan_count=0,
                total_agent_invocations=0,
                error_message=(
                    "Your request is outside the scope of Software Development Life Cycle (SDLC) workflows. "
                    "The Dynamic Workflow Orchestrator supports SDLC tasks such as Requirements Analysis (BRD), "
                    "Architecture Design, Sprint Planning, Microservice Development, and QA/Test Strategy. "
                    "Please provide a software engineering requirement or task."
                )
            )

        logger.info(f"Classified {len(intents)} consolidated agent task intents matching agents.json capabilities")

        # Scenario 2 & 3: SDLC Sequence Proofing & DAG construction
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
