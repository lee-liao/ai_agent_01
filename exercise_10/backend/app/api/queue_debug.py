from fastapi import APIRouter
from .queue_service import list_queue_items, get_waiting_count

router = APIRouter(prefix="/api/queue", tags=["QueueDebug"])

@router.get("/list")
async def queue_list():
    items = await list_queue_items()
    return {"count": len(items), "items": items}

@router.get("/count")
async def queue_count():
    count = await get_waiting_count()
    return {"waiting_customers": count}

