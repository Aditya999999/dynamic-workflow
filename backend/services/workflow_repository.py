import logging
from datetime import datetime
from models.workflow import WorkflowState
from services.mongo import MongoDBManager, get_mongo_manager

logger = logging.getLogger(__name__)


class WorkflowRepository:
    def __init__(self, mongo: MongoDBManager | None = None):
        self.mongo = mongo or get_mongo_manager()
        self._memory_store: dict[str, dict] = {}

    async def save_workflow(self, state: WorkflowState) -> None:
        state.updated_at = datetime.utcnow()
        doc = state.model_dump(mode="json")
        doc["_id"] = state.workflow_id

        if self.mongo.is_connected and self.mongo.db is not None:
            await self.mongo.db.dwf_workflows.replace_one(
                {"_id": state.workflow_id},
                doc,
                upsert=True
            )
        else:
            self._memory_store[state.workflow_id] = doc

    async def get_workflow(self, workflow_id: str) -> WorkflowState | None:
        if self.mongo.is_connected and self.mongo.db is not None:
            doc = await self.mongo.db.dwf_workflows.find_one({"_id": workflow_id})
            if doc:
                doc.pop("_id", None)
                return WorkflowState(**doc)
            return None
        else:
            doc = self._memory_store.get(workflow_id)
            if doc:
                d = dict(doc)
                d.pop("_id", None)
                return WorkflowState(**d)
            return None

    async def list_workflows(self, limit: int = 50) -> list[WorkflowState]:
        if self.mongo.is_connected and self.mongo.db is not None:
            cursor = self.mongo.db.dwf_workflows.find().sort("created_at", -1).limit(limit)
            results = []
            async for doc in cursor:
                doc.pop("_id", None)
                results.append(WorkflowState(**doc))
            return results
        else:
            docs = list(self._memory_store.values())
            docs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            results = []
            for doc in docs[:limit]:
                d = dict(doc)
                d.pop("_id", None)
                results.append(WorkflowState(**d))
            return results


_wf_repo_instance: WorkflowRepository | None = None


def get_workflow_repository() -> WorkflowRepository:
    global _wf_repo_instance
    if _wf_repo_instance is None:
        _wf_repo_instance = WorkflowRepository()
    return _wf_repo_instance
