import logging
from models.workflow import WorkflowState
from services.mongo import MongoDBManager, get_mongo_manager

logger = logging.getLogger(__name__)


class CheckpointStore:
    def __init__(self, mongo: MongoDBManager | None = None):
        self.mongo = mongo or get_mongo_manager()
        self._memory_checkpoints: dict[str, list[dict]] = {}

    async def save_checkpoint(self, state: WorkflowState, checkpoint_name: str) -> None:
        doc = {
            "workflow_id": state.workflow_id,
            "checkpoint_name": checkpoint_name,
            "plan_version": state.plan_version,
            "state": state.model_dump(mode="json")
        }
        if self.mongo.is_connected and self.mongo.db is not None:
            await self.mongo.db.dwf_checkpoints.insert_one(doc)
        else:
            if state.workflow_id not in self._memory_checkpoints:
                self._memory_checkpoints[state.workflow_id] = []
            self._memory_checkpoints[state.workflow_id].append(doc)


_checkpoint_instance: CheckpointStore | None = None


def get_checkpoint_store() -> CheckpointStore:
    global _checkpoint_instance
    if _checkpoint_instance is None:
        _checkpoint_instance = CheckpointStore()
    return _checkpoint_instance
