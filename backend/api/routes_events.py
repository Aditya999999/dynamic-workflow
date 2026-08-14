from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import StreamingResponse
from services.event_stream import EventStreamBroker, get_event_stream_broker

router = APIRouter(prefix="/api/dynamic-workflow", tags=["Event Streaming"])


@router.get("/{workflow_id}/events")
async def stream_workflow_events(
    workflow_id: str,
    after_sequence: int = Query(default=0),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    broker: EventStreamBroker = Depends(get_event_stream_broker)
):
    """Streams workflow execution events in real-time via Server-Sent Events (SSE)."""
    start_seq = after_sequence
    if last_event_id and last_event_id.isdigit():
        start_seq = max(start_seq, int(last_event_id))

    return StreamingResponse(
        broker.subscribe(workflow_id, after_sequence=start_seq),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
