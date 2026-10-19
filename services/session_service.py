import secrets
from functools import lru_cache
from redis.asyncio import Redis
from core.config import settings

PREFIX = "session:"

class SessionService:
    def __init__(self, client: Redis):
        self.client = client

    async def create(self, user_id: int, login: str) -> str:
        session_id = secrets.token_urlsafe(32)  # непредсказуемый идентификатор
        key = PREFIX + session_id
        # Хэш: id пользователя и логин (логин нужен Lua-скрипту, чтобы показать пользователей сессий)
        await self.client.hset(key, mapping={"user_id": user_id, "login": login})
        await self.client.expire(key, settings.SESSION_TTL_SECONDS)
        return session_id

    async def get_user_id(self, session_id: str | None) -> int | None:
        if not session_id:
            return None
        value = await self.client.hget(PREFIX + session_id, "user_id")
        return int(value) if value is not None else None

    async def destroy(self, session_id: str | None) -> None:
        if session_id:
            await self.client.delete(PREFIX + session_id)


@lru_cache(maxsize=1)
def get_redis() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_session_service() -> SessionService:
    return SessionService(get_redis())
