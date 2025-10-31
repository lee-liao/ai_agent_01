import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..state import get_or_create_queue

router = APIRouter(prefix="/api/stream", tags=["Streaming"])


@router.get("/suggestions/{call_id}")
async def stream_suggestions(call_id: str):
    queue = get_or_create_queue(call_id)

    async def event_generator():
        while True:
            payload = await queue.get()
            data = json.dumps(payload)
            yield f"data: {data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


