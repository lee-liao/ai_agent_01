import json
from typing import Optional, List, Dict
from datetime import datetime

from redis.asyncio import Redis
from ..config import settings


QUEUE_LIST_KEY = "queue:waiting_call_ids"


def get_redis() -> Redis:
    return Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        username=settings.REDIS_USERNAME,
        password=settings.REDIS_PASSWORD,
    )


async def enqueue_waiting_customer(customer_name: str, account_number: Optional[str], call_id: str) -> None:
    r = get_redis()
    # Store customer info in a hash keyed by call_id
    await r.hset(f"queue:item:{call_id}", mapping={
        "customer_name": customer_name,
        "account_number": account_number or "",
        "call_id": call_id,
        "timestamp": datetime.utcnow().isoformat(),
    })
    # Append call_id to FIFO list
    await r.rpush(QUEUE_LIST_KEY, call_id)


async def dequeue_top() -> Optional[Dict]:
    r = get_redis()
    call_id = await r.lpop(QUEUE_LIST_KEY)
    if not call_id:
        return None
    item_key = f"queue:item:{call_id}"
    data = await r.hgetall(item_key)
    await r.delete(item_key)
    return data or None


async def dequeue_by_account_number(account_number: str) -> Optional[Dict]:
    r = get_redis()
    ids: List[str] = await r.lrange(QUEUE_LIST_KEY, 0, -1)
    target_id: Optional[str] = None
    for cid in ids:
        info = await r.hgetall(f"queue:item:{cid}")
        if info and info.get("account_number") == account_number:
            target_id = cid
            break
    if not target_id:
        return None
    # Remove from list (first occurrence) and return the item
    await r.lrem(QUEUE_LIST_KEY, 1, target_id)
    item_key = f"queue:item:{target_id}"
    data = await r.hgetall(item_key)
    await r.delete(item_key)
    return data or None


async def remove_from_queue(call_id: str) -> None:
    r = get_redis()
    await r.lrem(QUEUE_LIST_KEY, 1, call_id)
    await r.delete(f"queue:item:{call_id}")


async def list_queue_items() -> List[Dict]:
    r = get_redis()
    ids: List[str] = await r.lrange(QUEUE_LIST_KEY, 0, -1)
    items: List[Dict] = []
    for cid in ids:
        info = await r.hgetall(f"queue:item:{cid}")
        if info:
            items.append({
                "customer_name": info.get("customer_name"),
                "account_number": info.get("account_number"),
                "waiting_since": info.get("timestamp"),
                "call_id": info.get("call_id"),
            })
    return items


async def get_waiting_count() -> int:
    r = get_redis()
    return await r.llen(QUEUE_LIST_KEY)


async def get_queue_position(call_id: str) -> Optional[int]:
    r = get_redis()
    ids: List[str] = await r.lrange(QUEUE_LIST_KEY, 0, -1)
    for idx, cid in enumerate(ids):
        if cid == call_id:
            return idx + 1
    return None
