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
    """Remove and return the first waiting customer from the queue (FIFO)"""
    print(f"🔄 dequeue_top() called - attempting to remove top customer from queue")
    r = get_redis()  # This was missing!
    script = """
    local queue_key = KEYS[1]
    local item_base = ARGV[1]
    
    -- Get the call_id of the first item in the queue
    local call_id = redis.call('lpop', queue_key)
    if not call_id then
        return nil
    end
    
    -- Get the item details
    local fields = redis.call('hgetall', item_base .. call_id)
    
    -- Convert to map
    local result = {}
    for i = 1, #fields, 2 do
        result[fields[i]] = fields[i + 1]
    end
    result['call_id'] = call_id
    
    -- Delete the item hash
    redis.call('del', item_base .. call_id)
    
    return result
    """
    
    res = await r.eval(script, 1, QUEUE_LIST_KEY, "queue:item:")
    
    if res:
        print(f"✅ Top customer {res.get('call_id', 'unknown')} dequeued from queue")
        # Add to active conversations to prevent duplicate matches
        from .calls import active_conversations
        active_conversations[res['call_id']] = {
            "customer_call_id": res['call_id'],
            "customer_name": res.get('customer_name'),
            "account_number": res.get('account_number'),
            "status": "matched"
        }
    else:
        print(f"⚠️ No customers found in queue to dequeue")
    
    return res


async def dequeue_by_account_number(account_number: str) -> Optional[Dict]:
    print(f"🔄 dequeue_by_account_number() called for account {account_number}")
    r = get_redis()
    # Lua script: scan list, find first id whose hash field account_number matches, remove and return full item
    script = """
    local list = KEYS[1]
    local prefix = ARGV[1]
    local target_acc = ARGV[2]
    local ids = redis.call('LRANGE', list, 0, -1)
    for _, id in ipairs(ids) do
      local key = prefix .. id
      local acc = redis.call('HGET', key, 'account_number')
      if acc == target_acc then
        redis.call('LREM', list, 1, id)
        local data = redis.call('HGETALL', key)
        redis.call('DEL', key)
        local result = {id}
        for i=1,#data do table.insert(result, data[i]) end
        return result
      end
    end
    return nil
    """
    res = await r.eval(script, 1, QUEUE_LIST_KEY, "queue:item:", account_number)
    
    if res:
        call_id = res[0]
        print(f"✅ Customer with account {account_number} ({call_id}) dequeued by account number")
        # Redis returns a flat array: [id, field1, value1, field2, value2, ...]
        fields = res[1:]
        item: Dict[str, str] = {fields[i]: fields[i+1] for i in range(0, len(fields), 2)} if fields else {}
        if call_id:
            item["call_id"] = call_id
        # Add to active conversations to prevent duplicate matches
        from .calls import active_conversations
        active_conversations[call_id] = {
            "customer_call_id": call_id,
            "customer_name": item.get('customer_name'),
            "account_number": item.get('account_number'),
            "status": "matched"
        }
        return item
    else:
        print(f"⚠️ No customer found with account number {account_number} to dequeue")
        return None


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


async def find_call_id_by_account(account_number: str) -> Optional[str]:
    r = get_redis()
    ids: List[str] = await r.lrange(QUEUE_LIST_KEY, 0, -1)
    for cid in ids:
        acc = await r.hget(f"queue:item:{cid}", "account_number")
        if acc == account_number:
            return cid
    return None
