import re
import logging
from typing import Any
from models.agents import AgentEndpoint

logger = logging.getLogger(__name__)


class AgentPayloadSchemaAdapter:
    """
    Adapts and validates input payloads against the agent's request_schema from agents.json.
    Automatically populates required fields (conversation_id, workspace_id, user_message, language, agent_feed, etc.)
    from runtime context and previous artifacts, ensuring smooth artifact & context chaining between agents.
    """

    @classmethod
    def adapt_payload(
        cls,
        endpoint: AgentEndpoint,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
        workflow_id: str | None = None,
        node_id: str | None = None,
        agent_id: str | None = None
    ) -> dict[str, Any]:
        context = context or {}
        adapted = dict(input_data or {})

        schema = endpoint.request_schema or {}
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])

        # 1. Resolve core standard fields from runtime context
        resolved_workspace_id = (
            adapted.get("workspace_id")
            or context.get("workspace_id")
            or "default_workspace"
        )

        resolved_conversation_id = (
            adapted.get("conversation_id")
            or context.get("conversation_id")
            or workflow_id
            or context.get("workflow_id")
            or "default_conv"
        )

        # Resolve primary prompt / message content across aliases
        raw_message_text = (
            adapted.get("user_message")
            or adapted.get("prompt")
            or adapted.get("message")
            or adapted.get("requirements")
            or context.get("query")
            or ""
        )

        # 2. Fill standard properties defined in schema or required list
        if "workspace_id" in properties or "workspace_id" in required_fields:
            adapted["workspace_id"] = resolved_workspace_id

        if "conversation_id" in properties or "conversation_id" in required_fields:
            adapted["conversation_id"] = resolved_conversation_id

        if "user_message" in properties or "user_message" in required_fields:
            adapted["user_message"] = raw_message_text

        if "prompt" in properties or "prompt" in required_fields:
            adapted["prompt"] = raw_message_text

        if "message" in properties or "message" in required_fields:
            adapted["message"] = raw_message_text

        if "requirements" in properties or "requirements" in required_fields:
            adapted["requirements"] = raw_message_text

        # 3. Smart Language resolution for Developer and Code Generation endpoints
        if "language" in properties or "language" in required_fields:
            if not adapted.get("language"):
                extracted_lang = cls._extract_language_from_context(raw_message_text, context)
                adapted["language"] = extracted_lang or "Python"
                logger.info(f"Resolved programming language '{adapted['language']}' for endpoint '{endpoint.name}'")

        if "agent_id" in properties or "agent_id" in required_fields:
            if "agent_id" not in adapted or adapted["agent_id"] is None:
                prop_type = properties.get("agent_id", {}).get("type", "string")
                adapted["agent_id"] = 1 if prop_type == "integer" else (agent_id or "1")

        # In multi-agent DAG pipelines, workflow_job_id and job_id must reference the shared workflow_id
        # (or resolved conversation_id) so downstream agents can locate artifacts created by upstream jobs in shared storage.
        shared_workflow_job_id = workflow_id or resolved_conversation_id or node_id
        adapted["job_id"] = adapted.get("job_id") if (adapted.get("job_id") and adapted.get("job_id") != node_id) else shared_workflow_job_id
        adapted["workflow_job_id"] = adapted.get("workflow_job_id") if (adapted.get("workflow_job_id") and adapted.get("workflow_job_id") != node_id) else shared_workflow_job_id

        # 4. Smart agent_feed construction from previous artifacts & dependencies
        if "agent_feed" in properties or "agent_feed" in required_fields:
            feed_items = cls._build_agent_feed(agent_id, node_id, context, adapted.get("agent_feed"))
            adapted["agent_feed"] = feed_items
            logger.info(f"Populated agent_feed for {agent_id} ({node_id}): {feed_items}")

        # 5. Check for any remaining required fields in the schema and provide safe, non-empty defaults
        for req_field in required_fields:
            if req_field not in adapted or adapted[req_field] is None:
                prop_info = properties.get(req_field, {})
                prop_type = prop_info.get("type", "string")
                min_len = prop_info.get("minLength", 0)

                if isinstance(prop_type, list):
                    prop_type = next((t for t in prop_type if t != "null"), "string")

                if prop_type == "string":
                    val = context.get(req_field, "")
                    if min_len >= 1 and not val:
                        val = raw_message_text or f"default_{req_field}"
                    adapted[req_field] = val
                elif prop_type == "array":
                    adapted[req_field] = []
                elif prop_type == "object":
                    adapted[req_field] = {}
                elif prop_type == "boolean":
                    adapted[req_field] = False
                elif prop_type in ["integer", "number"]:
                    adapted[req_field] = 0

                logger.warning(
                    f"Auto-populated missing required field '{req_field}' with default for endpoint '{endpoint.name}'"
                )

        logger.info(
            f"Adapted payload for agent='{agent_id}', endpoint='{endpoint.name}': keys={list(adapted.keys())}"
        )
        return adapted

    @classmethod
    def _build_agent_feed(
        cls,
        agent_id: str | None,
        node_id: str | None,
        context: dict[str, Any],
        existing_feed: list[str] | None
    ) -> list[str]:
        """Constructs a comprehensive feed list referencing all prior artifacts, artifact names, and upstream job IDs."""
        feed: set[str] = set(existing_feed or [])

        # Include workflow ID and conversation ID
        if context.get("workflow_id"):
            feed.add(str(context["workflow_id"]))
        if context.get("conversation_id"):
            feed.add(str(context["conversation_id"]))

        # Include prior artifact IDs and artifact names
        artifacts = context.get("artifacts", [])
        for art in artifacts:
            if hasattr(art, "artifact_id") and art.artifact_id:
                feed.add(str(art.artifact_id))
            elif isinstance(art, dict) and art.get("artifact_id"):
                feed.add(str(art.get("artifact_id")))

            if hasattr(art, "name") and art.name:
                feed.add(str(art.name))
                name_clean = str(art.name).replace(".md", "").replace(".json", "")
                feed.add(name_clean)
            elif isinstance(art, dict) and art.get("name"):
                feed.add(str(art.get("name")))
                name_clean = str(art.get("name")).replace(".md", "").replace(".json", "")
                feed.add(name_clean)

        # Include upstream dependency node IDs
        depends_on = context.get("depends_on", [])
        for dep in depends_on:
            if dep:
                feed.add(str(dep))

        # Default canonical feed tags based on agent role
        if agent_id == "architect":
            feed.update(["brd", "BRD", "BRD_Document", "BRD_Document.md", "requirements", "business-analyst", "business_analyst", "create_brd"])
        elif agent_id == "developer":
            feed.update(["architecture", "Architecture_Design.md", "Architecture_Design", "brd", "BRD_Document.md", "design", "architect", "business-analyst"])
        elif agent_id == "product-owner":
            feed.update(["brd", "BRD_Document.md", "architecture", "Architecture_Design.md", "business-analyst"])
        elif agent_id == "qe":
            feed.update(["brd", "architecture", "developer", "code", "BRD_Document.md", "Architecture_Design.md"])

        # Ensure feed is non-empty
        if not feed:
            feed.add("workflow_start")

        return list(feed)

    @classmethod
    def _extract_language_from_context(cls, text: str, context: dict[str, Any]) -> str | None:
        """Searches prompt, query, and previous artifact summaries for programming language mentions."""
        combined = f"{text} {context.get('query', '')}".lower()
        
        artifacts = context.get("artifacts", [])
        for art in artifacts:
            if hasattr(art, "summary") and art.summary:
                combined += f" {art.summary.lower()}"
            elif isinstance(art, dict) and art.get("summary"):
                combined += f" {art.get('summary', '').lower()}"

        language_map = {
            "python": "Python",
            "typescript": "TypeScript",
            "javascript": "JavaScript",
            "node": "Node.js",
            "golang": "Go",
            "java": "Java",
            "c#": "C#",
            "csharp": "C#",
            ".net": "C#",
            "rust": "Rust",
            "cpp": "C++",
            "c++": "C++",
            "php": "PHP",
            "ruby": "Ruby"
        }

        for keyword, lang_name in language_map.items():
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, combined):
                return lang_name

        return None
