from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import delete, exists, false, func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from core.current_user import CurrentUser, get_current_user, get_optional_user
from db.session import get_db
from models.like import Like
from models.period import Period
from schemas.period import LikeIn, LikeOut, PeriodDetail, PeriodFeed, PeriodPublish, PeriodTile
from services.minio_service import MinioService, get_minio_service

router = APIRouter(prefix="/api/periods", tags=["periods"])
UNAUTHORIZED = {401: {"description": "Не авторизован"}}

def _likes_count():
    return (
        select(func.count(Like.id))
        .where(Like.period_id == Period.id)
        .correlate(Period)
        .scalar_subquery()
    )

def _is_liked(user_id: int | None):
    if user_id is None:
        return false()
    return exists().where(Like.period_id == Period.id, Like.user_id == user_id).correlate(Period)

@router.get(
    "",
    response_model=list[PeriodTile],
    summary="Список периодов",
    description="Опубликованные периоды с фильтром по количеству дней. Доступно гостю; для гостя is_mine всегда 0.",
)
async def list_periods(
    min_days: int | None = Query(None, ge=0, description="Минимальное количество дней"),
    user: CurrentUser | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Period, _likes_count().label("likes_count")).where(Period.status == "published")
    if min_days is not None:
        stmt = stmt.where(Period.days_count >= min_days)
    stmt = stmt.order_by(Period.order_number, Period.id)

    rows = (await db.execute(stmt)).all()
    return [
        {
            "id": period.id,
            "title": period.title,
            "days_count": period.days_count,
            "image_url": period.image_url,
            "likes_count": likes_count,
            "is_mine": int(user is not None and period.creator_id == user.id),
        }
        for period, likes_count in rows
    ]


@router.get(
    "/feed",
    response_model=PeriodFeed,
    summary="Лента (первый период)",
    description="Один период ленты. Доступно гостю; для гостя is_liked всегда 0.",
    responses={404: {"description": "Опубликованных периодов нет"}},
)
@router.get(
    "/feed/{period_id}",
    response_model=PeriodFeed,
    summary="Лента (период по id или следующий)",
    description="С next=false возвращает период с этим id, с next=true следующий по порядку (по кругу). Доступно гостю.",
    responses={404: {"description": "Период не найден"}},
)
async def get_feed(
    period_id: int | None = None,
    next: bool = False,
    user: CurrentUser | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(
        Period,
        _likes_count().label("likes_count"),
        _is_liked(user.id if user else None).label("is_liked"),
    ).where(Period.status == "published")
    order = (Period.order_number, Period.id)

    row = None
    if period_id is not None and not next:
        row = (await db.execute(base.where(Period.id == period_id))).first()
        if row is None:
            raise HTTPException(status_code=404, detail="Услуга не найдена")
    else:
        if period_id is not None:
            current = (
                await db.execute(
                    select(Period.order_number, Period.id).where(
                        Period.id == period_id, Period.status == "published"
                    )
                )
            ).first()
            if current is not None:
                row = (
                    await db.execute(
                        base.where(
                            tuple_(Period.order_number, Period.id)
                            > tuple_(current.order_number, current.id)
                        )
                        .order_by(*order)
                        .limit(1)
                    )
                ).first()
        if row is None:
            row = (await db.execute(base.order_by(*order).limit(1))).first()
        if row is None:
            raise HTTPException(status_code=404, detail="Опубликованных услуг нет")

    period, likes_count, is_liked = row
    return {
        "id": period.id,
        "title": period.title,
        "description": period.description,
        "order_number": period.order_number,
        "days_count": period.days_count,
        "video_url": period.video_url,
        "likes_count": likes_count,
        "is_liked": int(is_liked),
    }


@router.get(
    "/draft",
    response_model=PeriodDetail,
    summary="Получить черновик",
    description="Черновик текущего пользователя (не более одного). Только для авторизованного.",
    responses={**UNAUTHORIZED, 404: {"description": "У пользователя нет черновика"}},
)
async def get_draft(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Period).where(Period.status == "draft", Period.creator_id == user.id)
    period = (await db.execute(stmt)).scalar_one_or_none()
    if period is None:
        raise HTTPException(status_code=404, detail="У пользователя нет черновика")
    return period


async def _get_own_period(db: AsyncSession, period_id: int, user: CurrentUser) -> Period:
    period = (
        await db.execute(select(Period).where(Period.id == period_id, Period.status != "deleted"))
    ).scalar_one_or_none()
    if period is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    if period.creator_id != user.id:
        raise HTTPException(status_code=403, detail="Это услуга другого пользователя")
    return period


@router.post(
    "",
    response_model=PeriodDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить период (черновик)",
    description="Создаёт черновик: название, фото и видео. Автор берётся из сессии. Только для авторизованного.",
    responses={**UNAUTHORIZED, 400: {"description": "Неверный тип или пустой файл"}, 409: {"description": "Черновик уже есть"}},
)
async def create_period(
    title: str = Form(..., min_length=1, max_length=100),
    image: UploadFile = File(...),
    video: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio: MinioService = Depends(get_minio_service),
):
    has_draft = (
        await db.execute(select(Period.id).where(Period.status == "draft", Period.creator_id == user.id))
    ).first()
    if has_draft is not None:
        raise HTTPException(status_code=409, detail="У пользователя уже есть черновик")

    image_name = await run_in_threadpool(minio.upload, image.file, image.content_type, "image")
    video_name = await run_in_threadpool(minio.upload, video.file, video.content_type, "video")

    period = Period(
        title=title,
        status="draft",
        creator_id=user.id,
        image_url=image_name,
        video_url=video_name,
    )
    db.add(period)
    await db.commit()
    await db.refresh(period)
    return period


@router.put(
    "/{period_id}",
    response_model=PeriodDetail,
    summary="Опубликовать период",
    description="Заполняет описание, порядок и количество дней, переводит черновик в «опубликован». Только создатель.",
    responses={**UNAUTHORIZED, 403: {"description": "Чужой период"}, 404: {"description": "Период не найден"}, 409: {"description": "Это не черновик"}},
)
async def publish_period(
    period_id: int,
    body: PeriodPublish,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    period = await _get_own_period(db, period_id, user)
    if period.status != "draft":
        raise HTTPException(status_code=409, detail="Опубликовать можно только черновик")

    period.description = body.description
    period.order_number = body.order_number
    period.days_count = body.days_count
    period.status = "published"
    period.published_at = func.now()
    await db.commit()
    return period


@router.delete(
    "/{period_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить период",
    description="Мягкое удаление своего периода (статус «удалён»). Только создатель.",
    responses={**UNAUTHORIZED, 403: {"description": "Чужой период"}, 404: {"description": "Период не найден"}},
)
async def delete_period(
    period_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    period = await _get_own_period(db, period_id, user)
    period.status = "deleted"
    await db.commit()

@router.post(
    "/{period_id}/like",
    response_model=LikeOut,
    summary="Поставить или убрать лайк",
    description="like=1 поставить, 0 убрать. Повтор безопасен. Только для авторизованного.",
    responses={**UNAUTHORIZED, 404: {"description": "Период не найден"}},
)
async def set_like(
    period_id: int,
    body: LikeIn,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    published = (
        await db.execute(select(Period.id).where(Period.id == period_id, Period.status == "published"))
    ).first()
    if published is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    if body.like == 1:
        already = (
            await db.execute(select(Like.id).where(Like.period_id == period_id, Like.user_id == user.id))
        ).first()
        if already is None:
            db.add(Like(user_id=user.id, period_id=period_id))
    else:
        await db.execute(delete(Like).where(Like.period_id == period_id, Like.user_id == user.id))
    await db.commit()

    likes_count = (
        await db.execute(select(func.count(Like.id)).where(Like.period_id == period_id))
    ).scalar_one()
    return {"likes_count": likes_count}
