from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from core.current_user import CurrentUser, get_current_user
from core.security import hash_password
from db.session import get_db
from models.user import User
from schemas.user import UserCredentials, UserOut

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(body: UserCredentials, db: AsyncSession = Depends(get_db)):
    """Регистрация: логин должен быть свободен, пароль сохраняется только в виде хэша."""
    taken = (await db.execute(select(User.id).where(User.login == body.login))).first()
    if taken is not None:
        raise HTTPException(status_code=409, detail="Пользователь с таким логином уже существует")

    user = User(login=body.login, password=await run_in_threadpool(hash_password, body.password))
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:  # два запроса с одним логином одновременно
        await db.rollback()
        raise HTTPException(status_code=409, detail="Пользователь с таким логином уже существует")
    await db.refresh(user)
    return user


@router.post("/login", response_model=UserOut)
async def login_user(
    body: UserCredentials,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Заглушка для 4-й лабораторной: пароль не проверяется, возвращается текущий пользователь."""
    user = (await db.execute(select(User).where(User.id == current.id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_user():
    """Заглушка для 4-й лабораторной."""
