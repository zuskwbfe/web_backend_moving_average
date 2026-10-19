from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyCookie

from core.config import settings
from services.session_service import SessionService, get_session_service

# Схема для Swagger: кнопка Authorize и замочки на методах создателя
cookie_scheme = APIKeyCookie(
    name=settings.SESSION_COOKIE_NAME,
    scheme_name="SessionCookie",
    description="Кука сессии, которую выставляет POST /api/users/login",
    auto_error=False,
)


@dataclass(frozen=True)
class CurrentUser:
    id: int


async def get_optional_user(
    request: Request,
    sessions: SessionService = Depends(get_session_service),
) -> CurrentUser | None:
    """Для методов чтения: гость (None) тоже допустим."""
    user_id = await sessions.get_user_id(request.cookies.get(settings.SESSION_COOKIE_NAME))
    return CurrentUser(id=user_id) if user_id is not None else None


async def get_current_user(
    session_id: str | None = Depends(cookie_scheme),
    sessions: SessionService = Depends(get_session_service),
) -> CurrentUser:
    """Для методов создателя: без сессии 401."""
    user_id = await sessions.get_user_id(session_id)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация")
    return CurrentUser(id=user_id)
