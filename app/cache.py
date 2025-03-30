import json
import redis
from datetime import datetime
from typing import Optional, Dict, Any

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

def get_cached_link(short_code: str) -> Optional[Dict[str, Any]]:
    cached_data = redis_client.get(f"link:{short_code}")
    if cached_data:
        return json.loads(cached_data)
    return None

def set_cached_link(short_code: str, link_data: Dict[str, Any], expire_seconds: int = 3600) -> None:
    redis_client.setex(
        f"link:{short_code}",
        expire_seconds,
        json.dumps(link_data)
    )

def delete_cached_link(short_code: str) -> None:
    redis_client.delete(f"link:{short_code}")

def increment_access_count(short_code: str) -> int:
    return redis_client.incr(f"link:{short_code}:access_count")

def get_link_stats(short_code: str) -> Optional[Dict[str, Any]]:
    cached_data = redis_client.get(f"link:{short_code}:stats")
    if cached_data:
        return json.loads(cached_data)
    return None

def set_link_stats(short_code: str, stats_data: Dict[str, Any], expire_seconds: int = 3600) -> None:
    redis_client.setex(
        f"link:{short_code}:stats",
        expire_seconds,
        json.dumps(stats_data)
    ) 