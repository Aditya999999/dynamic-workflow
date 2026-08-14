import asyncio
import json
import logging
from typing import AsyncGenerator
from models.events import WorkflowEvent
from services.event_repository import EventRepository, get_event_repository
from config.settings import get_settings

logger = logging.getLogger(__name__)


class EventStreamBroker:
    def __init__(self, event_repo: EventRepository | None = None):
        self.event_repo = event_repo or get_event_repository()
        self.settings = get_settings()
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    async def broadcast(self, event: WorkflowEvent) -> None:
        # First persist the event
        await self.event_repo.log_event(event)

        # Broadcast to active SSE listeners
        workflow_id = event.workflow_id
        if workflow_id in self._subscribers:
            dead_queues = []
            for queue in self._subscribers[workflow_id]:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    dead_queues.append(queue)
            for dq in dead_queues:
                self._subscribers[workflow_id].remove(dq)

    async def subscribe(
        self,
        workflow_id: str,
        after_sequence: int = 0
    ) -> AsyncGenerator[str, None]:
        queue: asyncio.Queue[WorkflowEvent] = asyncio.Queue(maxsize=100)
        if workflow_id not in self._subscribers:
            self._subscribers[workflow_id] = []
        self._subscribers[workflow_id].append(queue)

        try:
            # 1. Replay past events if reconnecting or starting
            past_events = await self.event_repo.get_events(workflow_id, after_sequence=after_sequence)
            for event in past_events:
                yield f"id: {event.sequence_number}\nevent: {event.event_type}\ndata: {json.dumps(event.model_dump(mode='json'))}\n\n"

            # 2. Stream live events with heartbeat
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=self.settings.dwf_event_heartbeat_seconds)
                    yield f"id: {event.sequence_number}\nevent: {event.event_type}\ndata: {json.dumps(event.model_dump(mode='json'))}\n\n"
                except asyncio.TimeoutError:
                    # Send SSE heartbeat
                    yield f": heartbeat\n\n"
        finally:
            if workflow_id in self._subscribers and queue in self._subscribers[workflow_id]:
                self._subscribers[workflow_id].remove(queue)


_stream_broker_instance: EventStreamBroker | None = None


def get_event_stream_broker() -> EventStreamBroker:
    global _stream_broker_instance
    if _stream_broker_instance is None:
        _stream_broker_instance = EventStreamBroker()
    return _stream_broker_instance
