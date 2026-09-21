from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.period import Period
from models.like import Like
from models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

CURRENT_USER_ID = 1

DEFAULT_IMAGE_URL = "/static/img/default.png"
DEFAULT_VIDEO_URL = "/static/img/default.mp4"

DAY_WORD_FORMS = {"one": "день", "few": "дня", "many": "дней"}


def get_days_word(count: int) -> str:
    remainder_100 = abs(count) % 100
    remainder_10 = remainder_100 % 10
    if 11 <= remainder_100 <= 14:
        form = "many"
    elif remainder_10 == 1:
        form = "one"
    elif 2 <= remainder_10 <= 4:
        form = "few"
    else:
        form = "many"
    return DAY_WORD_FORMS[form]


def days_label(count: int | None) -> str:
    if count is None:
        return ""
    return f"{count} {get_days_word(count)}"


def resolve_media(period: Period) -> tuple[str, str]:
    """Возвращает (image_url, video_url), подставляя значения по умолчанию, если поля пустые."""
    image_url = period.image_url or DEFAULT_IMAGE_URL
    video_url = period.video_url or DEFAULT_VIDEO_URL
    return image_url, video_url


@router.get("/")
async def get_catalog(request: Request, min_days: str = None, db: AsyncSession = Depends(get_db)):
    parsed_min_days = None
    if min_days:
        try:
            parsed_min_days = int(float(min_days.replace(",", ".")))
        except ValueError:
            parsed_min_days = None

    stmt = select(Period).where(Period.status == "published")
    if parsed_min_days is not None:
        stmt = stmt.where(Period.days_count >= parsed_min_days)
    stmt = stmt.order_by(Period.order_number)

    result = await db.execute(stmt)
    periods = result.scalars().all()

    likes_result = await db.execute(
        select(Like.period_id, func.count(Like.id)).group_by(Like.period_id)
    )
    likes_by_period = {row[0]: row[1] for row in likes_result.all()}

    enriched = []
    for p in periods:
        image_url, _ = resolve_media(p)
        enriched.append({
            "id": p.id,
            "title": p.title,
            "days_count": p.days_count,
            "days_label": days_label(p.days_count),
            "image_url": image_url,
            "likes_count": likes_by_period.get(p.id, 0),
        })

    return templates.TemplateResponse(
        request=request,
        name="period_list.html",
        context={"periods": enriched, "min_days": min_days}
    )


# ===== 2. GET /period/{id} — лента, через ORM =====
@router.get("/period/{period_id}")
async def get_period_detail(request: Request, period_id: int, next: bool = False, db: AsyncSession = Depends(get_db)):
    if next:
        # Узнаём order_number текущей карточки одним лёгким запросом
        current_order_result = await db.execute(
            select(Period.order_number).where(Period.id == period_id)
        )
        current_order = current_order_result.scalar_one_or_none()

        # Ищем следующую опубликованную карточку ПО ПОРЯДКУ — один запрос, LIMIT 1
        next_stmt = (
            select(Period)
            .where(Period.status == "published", Period.order_number > current_order)
            .order_by(Period.order_number.asc())
            .limit(1)
        )
        result = await db.execute(next_stmt)
        period = result.scalar_one_or_none()

        if period is None:
            # Дошли до конца — заворачиваем на самую первую опубликованную карточку
            first_stmt = (
                select(Period)
                .where(Period.status == "published")
                .order_by(Period.order_number.asc())
                .limit(1)
            )
            result = await db.execute(first_stmt)
            period = result.scalar_one_or_none()
    else:
        # Обычный прямой переход — тоже ровно одна строка из БД
        stmt = select(Period).where(Period.id == period_id, Period.status == "published")
        result = await db.execute(stmt)
        period = result.scalar_one_or_none()

    if period is None:
        # Удалённые/несуществующие услуги смотреть нельзя — уходим на список
        return RedirectResponse(url="/", status_code=303)

    image_url, video_url = resolve_media(period)

    likes_result = await db.execute(
        select(func.count(Like.id)).where(Like.period_id == period.id)
    )
    likes_count = likes_result.scalar_one()

    return templates.TemplateResponse(
        request=request,
        name="period_feed.html",
        context={
            "period": period,
            "image_url": image_url,
            "video_url": video_url,
            "likes_count": likes_count,
            "days_label": days_label(period.days_count),
        }
    )


# ===== 3. GET /draft — черновик текущего пользователя, через ORM =====
@router.get("/draft")
async def get_draft(request: Request, db: AsyncSession = Depends(get_db)):
    stmt = select(Period).where(
        Period.status == "draft",
        Period.creator_id == CURRENT_USER_ID
    )
    result = await db.execute(stmt)
    draft = result.scalar_one_or_none()

    if draft is None:
        # У пользователя ещё нет черновика — показываем форму создания (шаг 1: название/фото/видео)
        return templates.TemplateResponse(
            request=request,
            name="period_draft.html",
            context={"period": None}
        )

    # Черновик уже есть — показываем форму публикации (шаг 2: описание + поля темы)
    image_url, video_url = resolve_media(draft)
    return templates.TemplateResponse(
        request=request,
        name="period_draft.html",
        context={"period": draft, "image_url": image_url, "video_url": video_url}
    )


# ===== 4. POST создания черновика — через ORM =====
@router.post("/draft/create")
async def create_draft(
    title: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # Проверяем, что у пользователя ещё нет черновика (правило: не более одного)
    existing = await db.execute(
        select(Period).where(Period.status == "draft", Period.creator_id == CURRENT_USER_ID)
    )
    if existing.scalar_one_or_none() is not None:
        return RedirectResponse(url="/draft", status_code=303)

    new_period = Period(
        title=title,
        status="draft",
        creator_id=CURRENT_USER_ID,
        # image_url/video_url оставляем пустыми — новые файлы в этой ЛР не сохраняются
    )
    db.add(new_period)
    await db.commit()

    return RedirectResponse(url="/draft", status_code=303)


# ===== 5. POST публикации черновика — через ORM =====
@router.post("/draft/publish")
async def publish_draft(
    description: str = Form(...),
    order_number: int = Form(...),
    days_count: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Period).where(Period.status == "draft", Period.creator_id == CURRENT_USER_ID)
    result = await db.execute(stmt)
    draft = result.scalar_one_or_none()

    if draft is not None:
        draft.description = description
        draft.order_number = order_number
        draft.days_count = days_count
        draft.status = "published"
        draft.published_at = func.now()
        await db.commit()

    return RedirectResponse(url="/", status_code=303)


# ===== 6. POST удаления — через курсор (сырой SQL), БЕЗ ORM =====
@router.post("/period/{period_id}/delete")
async def delete_period(period_id: int, db: AsyncSession = Depends(get_db)):
    update_query = """
        UPDATE periods
        SET status = 'deleted'
        WHERE id = :id
    """
    await db.execute(text(update_query), {"id": period_id})
    await db.commit()

    return RedirectResponse(url="/", status_code=303)
