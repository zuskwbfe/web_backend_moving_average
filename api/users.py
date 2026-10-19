from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from core.config import settings
from core.current_user import CurrentUser, get_current_user
from core.security import hash_password, verify_password
from db.session import get_db
from models.user import User
from schemas.user import UserCredentials, UserOut
from services.session_service import SessionService, get_session_service

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация",
    description="Создаёт пользователя. Логин должен быть свободен, пароль хранится только в виде хэша.",
    responses={409: {"description": "Пользователь с таким логином уже существует"}},
)
async def register_user(body: UserCredentials, db: AsyncSession = Depends(get_db)):
    taken = (await db.execute(select(User.id).where(User.login == body.login))).first()
    if taken is not None:
        raise HTTPException(status_code=409, detail="Пользователь с таким логином уже существует")

    user = User(login=body.login, password=await run_in_threadpool(hash_password, body.password))
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Пользователь с таким логином уже существует")
    await db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=UserOut,
    summary="Аутентификация",
    description="Проверяет логин и пароль, создаёт сессию в Redis и выставляет HttpOnly-куку session_id.",
    responses={401: {"description": "Неверный логин или пароль"}},
)
async def login_user(
    body: UserCredentials,
    response: Response,
    db: AsyncSession = Depends(get_db),
    sessions: SessionService = Depends(get_session_service),
):
    user = (await db.execute(select(User).where(User.login == body.login))).scalar_one_or_none()
    if user is None or not await run_in_threadpool(verify_password, body.password, user.password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    session_id = await sessions.create(user.id, user.login)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_id,
        max_age=settings.SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
    )
    return user


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Деавторизация",
    description="Удаляет сессию из Redis и куку в браузере. Требуется авторизация.",
    responses={401: {"description": "Не авторизован"}},
)
async def logout_user(
    request: Request,
    response: Response,
    _user: CurrentUser = Depends(get_current_user),
    sessions: SessionService = Depends(get_session_service),
):
    await sessions.destroy(request.cookies.get(settings.SESSION_COOKIE_NAME))
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
