from typing import Any
from models.workflow import StandardAgentResponse, NextAction


class ResponseNormalizer:
    """Transforms disparate agent response shapes into standardized StandardAgentResponse."""

    def normalize(self, agent_id: str, raw_response: dict[str, Any]) -> StandardAgentResponse:
        adapter_method = f"_normalize_{agent_id.replace('-', '_')}"
        adapter = getattr(self, adapter_method, self._normalize_generic)
        return adapter(raw_response)

    def _normalize_business_analyst(self, raw: dict[str, Any]) -> StandardAgentResponse:
        if raw.get("status") == "error" or not raw.get("success", True):
            return StandardAgentResponse(
                status="error",
                error_message=raw.get("message") or "BA Agent execution failed",
                result=raw
            )

        data = raw.get("data", {})
        next_action_data = data.get("next_action", {})
        next_action = NextAction(**next_action_data) if isinstance(next_action_data, dict) else NextAction(type="none")

        return StandardAgentResponse(
            status="completed",
            result=data,
            artifact_name=data.get("artifact_name", "BRD_Document.md"),
            artifact_type=data.get("artifact_type", "markdown"),
            artifact_summary=data.get("summary", "Business Requirements Document"),
            next_action=next_action,
            confidence=data.get("confidence", 1.0),
            metadata={"source_agent": "business-analyst", "raw_message": raw.get("message")}
        )

    def _normalize_architect(self, raw: dict[str, Any]) -> StandardAgentResponse:
        if raw.get("status") == "error":
            return StandardAgentResponse(
                status="error",
                error_message=raw.get("message") or "Architect Agent execution failed",
                result=raw
            )

        data = raw.get("data", {})
        next_action_data = data.get("next_action", {})
        next_action = NextAction(**next_action_data) if isinstance(next_action_data, dict) else NextAction(type="none")

        status_val = "needs_input" if raw.get("status") == "needs_input" or next_action.type in ["needs_input", "request_agent"] else "completed"

        return StandardAgentResponse(
            status=status_val,
            result=data,
            artifact_name=data.get("artifact_name", "Architecture_Design.md"),
            artifact_type=data.get("artifact_type", "markdown"),
            artifact_summary=data.get("summary", "System Architecture & Mermaid diagram"),
            next_action=next_action,
            confidence=data.get("confidence", 0.95),
            metadata={"source_agent": "architect"}
        )

    def _normalize_developer(self, raw: dict[str, Any]) -> StandardAgentResponse:
        if raw.get("status") == "error":
            return StandardAgentResponse(
                status="error",
                error_message=raw.get("message") or "Developer Agent execution failed",
                result=raw
            )

        data = raw.get("data", {})
        next_action_data = data.get("next_action", {})
        next_action = NextAction(**next_action_data) if isinstance(next_action_data, dict) else NextAction(type="none")

        return StandardAgentResponse(
            status="completed",
            result=data,
            artifact_name=data.get("artifact_name", "Implementation.py"),
            artifact_type=data.get("artifact_type", "code"),
            artifact_summary=data.get("summary", "FastAPI microservice implementation scaffold"),
            next_action=next_action,
            confidence=data.get("confidence", 0.95),
            metadata={"source_agent": "developer"}
        )

    def _normalize_product_owner(self, raw: dict[str, Any]) -> StandardAgentResponse:
        if raw.get("status") == "error":
            return StandardAgentResponse(
                status="error",
                error_message=raw.get("message") or "Product Owner Agent execution failed",
                result=raw
            )

        data = raw.get("data", {})
        next_action_data = data.get("next_action", {})
        next_action = NextAction(**next_action_data) if isinstance(next_action_data, dict) else NextAction(type="none")

        return StandardAgentResponse(
            status="completed",
            result=data,
            artifact_name=data.get("artifact_name", "Sprint_Plan.md"),
            artifact_type=data.get("artifact_type", "markdown"),
            artifact_summary=data.get("summary", "Sprint backlog prioritization and story points"),
            next_action=next_action,
            confidence=data.get("confidence", 0.97),
            metadata={"source_agent": "product-owner"}
        )

    def _normalize_qe(self, raw: dict[str, Any]) -> StandardAgentResponse:
        if raw.get("status") == "error":
            return StandardAgentResponse(
                status="error",
                error_message=raw.get("message") or "QE Agent execution failed",
                result=raw
            )

        data = raw.get("data", {})
        next_action_data = data.get("next_action", {})
        next_action = NextAction(**next_action_data) if isinstance(next_action_data, dict) else NextAction(type="none")

        return StandardAgentResponse(
            status="completed",
            result=data,
            artifact_name=data.get("artifact_name", "QE_Strategy.md"),
            artifact_type=data.get("artifact_type", "markdown"),
            artifact_summary=data.get("summary", "Test strategy and automated test coverage suite"),
            next_action=next_action,
            confidence=data.get("confidence", 0.99),
            metadata={"source_agent": "qe"}
        )

    def _normalize_generic(self, raw: dict[str, Any]) -> StandardAgentResponse:
        status_val = "error" if raw.get("status") == "error" else "completed"
        data = raw.get("data", raw)
        return StandardAgentResponse(
            status=status_val,
            result=data if isinstance(data, dict) else {"output": data},
            artifact_name=data.get("artifact_name") if isinstance(data, dict) else None,
            artifact_summary=data.get("summary") if isinstance(data, dict) else None,
            next_action=NextAction(type="none"),
            confidence=0.9
        )


_normalizer_instance: ResponseNormalizer | None = None


def get_response_normalizer() -> ResponseNormalizer:
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = ResponseNormalizer()
    return _normalizer_instance
