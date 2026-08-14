import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config.settings import get_settings

logger = logging.getLogger(__name__)


class MongoDBManager:
    def __init__(self):
        self.settings = get_settings()
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None
        self._connected: bool = False

    async def connect(self) -> bool:
        if self.settings.persistence_mode == "memory":
            logger.info("Running in explicit in-memory persistence mode.")
            self._connected = False
            return False

        try:
            self.client = AsyncIOMotorClient(
                self.settings.mongodb_uri,
                serverSelectionTimeoutMS=2000
            )
            # Check connection
            await self.client.admin.command("ping")
            self.db = self.client[self.settings.mongodb_database]
            self._connected = True
            logger.info(f"Connected to MongoDB database: {self.settings.mongodb_database}")

            # Ensure indexes
            await self._setup_indexes()
            return True
        except Exception as e:
            logger.warning(f"MongoDB connection failed ({str(e)}). Falling back to in-memory store.")
            self._connected = False
            return False

    async def _setup_indexes(self) -> None:
        if not self.db:
            return
        try:
            await self.db.dwf_workflows.create_index("workflow_id", unique=True)
            await self.db.dwf_events.create_index([("workflow_id", 1), ("sequence_number", 1)], unique=True)
            await self.db.dwf_artifacts.create_index("artifact_id", unique=True)
            await self.db.dwf_idempotency.create_index("key", unique=True)
        except Exception as e:
            logger.warning(f"Index creation notice: {e}")

    async def disconnect(self) -> None:
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("MongoDB connection closed.")

    @property
    def is_connected(self) -> bool:
        return self._connected


_mongo_manager: MongoDBManager | None = None


def get_mongo_manager() -> MongoDBManager:
    global _mongo_manager
    if _mongo_manager is None:
        _mongo_manager = MongoDBManager()
    return _mongo_manager
