import redis
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import Optional, Dict, Any

load_dotenv()

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

def get_cached_link(short_code: str) -> Optional[Dict[str, Any]]:
    cached_data = redis_client.get(f"link:{short_code}")
    if cached_data:
        return json.loads(cached_data)
    return None

def set_cached_link(short_code: str, link_data: Dict[str, Any]) -> None:
    redis_client.setex(
        f"link:{short_code}",
        3600, 
        json.dumps(link_data)
    )

def delete_cached_link(short_code: str) -> None:
    redis_client.delete(f"link:{short_code}")
    redis_client.delete(f"stats:{short_code}")

def increment_access_count(short_code: str) -> None:
    stats = get_link_stats(short_code) or {"access_count": 0}
    stats["access_count"] = stats.get("access_count", 0) + 1
    set_link_stats(short_code, stats)

def get_link_stats(short_code: str) -> Optional[Dict[str, Any]]:
    cached_stats = redis_client.get(f"stats:{short_code}")
    if cached_stats:
        return json.loads(cached_stats)
    return None

def set_link_stats(short_code: str, stats: Dict[str, Any]) -> None:
    redis_client.setex(
        f"stats:{short_code}",
        3600,
        json.dumps(stats)
    ) 