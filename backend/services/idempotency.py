import time
from typing import Any
from services.mongo import MongoDBManager, get_mongo_manager


class IdempotencyService:
    def __init__(self, mongo: MongoDBManager | None = None):
        self.mongo = mongo or get_mongo_manager()
        self._memory_keys: dict[str, dict] = {}

    async def check_or_set(self, key: str, ttl_seconds: int = 3600) -> bool:
        """Returns True if the key was freshly acquired, False if it was already locked/processed."""
        now = time.time()
        if self.mongo.is_connected and self.mongo.db is not None:
            try:
                res = await self.mongo.db.dwf_idempotency.update_one(
                    {"key": key, "expires_at": {"$gt": now}},
                    {"$setOnInsert": {"key": key, "created_at": now, "expires_at": now + ttl_seconds}},
                    upsert=True
                )
                return res.upserted_id is not None
            except Exception:
                return False
        else:
            if key in self._memory_keys and self._memory_keys[key]["expires_at"] > now:
                return False
            self._memory_keys[key] = {"created_at": now, "expires_at": now + ttl_seconds}
            return True


_idempotency_instance: IdempotencyService | None = None


def get_idempotency_service() -> IdempotencyService:
    global _idempotency_instance
    if _idempotency_instance is None:
        _idempotency_instance = IdempotencyService()
    return _idempotency_instance
