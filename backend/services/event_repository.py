import logging
from models.events import WorkflowEvent
from services.mongo import MongoDBManager, get_mongo_manager

logger = logging.getLogger(__name__)


class EventRepository:
    def __init__(self, mongo: MongoDBManager | None = None):
        self.mongo = mongo or get_mongo_manager()
        self._memory_events: dict[str, list[dict]] = {}

    async def log_event(self, event: WorkflowEvent) -> None:
        doc = event.model_dump(mode="json")
        if self.mongo.is_connected and self.mongo.db is not None:
            await self.mongo.db.dwf_events.insert_one(doc)
        else:
            if event.workflow_id not in self._memory_events:
                self._memory_events[event.workflow_id] = []
            self._memory_events[event.workflow_id].append(doc)

    async def get_events(self, workflow_id: str, after_sequence: int = 0) -> list[WorkflowEvent]:
        if self.mongo.is_connected and self.mongo.db is not None:
            query = {"workflow_id": workflow_id, "sequence_number": {"$gt": after_sequence}}
            cursor = self.mongo.db.dwf_events.find(query).sort("sequence_number", 1)
            results = []
            async for doc in cursor:
                doc.pop("_id", None)
                results.append(WorkflowEvent(**doc))
            return results
        else:
            evs = self._memory_events.get(workflow_id, [])
            filtered = [WorkflowEvent(**e) for e in evs if e.get("sequence_number", 0) > after_sequence]
            filtered.sort(key=lambda x: x.sequence_number)
            return filtered

    async def get_next_sequence_number(self, workflow_id: str) -> int:
        if self.mongo.is_connected and self.mongo.db is not None:
            latest = await self.mongo.db.dwf_events.find_one(
                {"workflow_id": workflow_id},
                sort=[("sequence_number", -1)]
            )
            return (latest["sequence_number"] + 1) if latest else 1
        else:
            evs = self._memory_events.get(workflow_id, [])
            return len(evs) + 1


_event_repo_instance: EventRepository | None = None


def get_event_repository() -> EventRepository:
    global _event_repo_instance
    if _event_repo_instance is None:
        _event_repo_instance = EventRepository()
    return _event_repo_instance
