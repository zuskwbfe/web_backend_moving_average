from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from data.collections import periods_db

router = APIRouter()
# Указываем, где искать HTML файлы
templates = Jinja2Templates(directory="templates")


# Словарь форм слова "день" в зависимости от числа
DAY_WORD_FORMS = {
    "one": "день",
    "few": "дня",
    "many": "дней",
}


def get_days_word(count: int) -> str:
    """Возвращает согласованную форму слова 'день' для числа count."""
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


def days_label(count: int) -> str:
    """Готовая фраза вида '31 день' / '92 дня' / '30 дней'."""
    return f"{count} {get_days_word(count)}"

@router.get("/")
def get_catalog(request: Request, min_days: str = None):
    # Поле фильтра — обычный текстовый/слайдер-инпут, парсим вручную
    parsed_min_days = None
    if min_days:
        try:
            parsed_min_days = int(float(min_days.replace(",", ".")))
        except ValueError:
            parsed_min_days = None

    published = [p for p in periods_db if p["status"] == "published"]

    enriched = []
    for p in published:
        if parsed_min_days is not None and p["days_count"] < parsed_min_days:
            continue
        enriched.append({
            **p,
            "likes_count": len(p["likes"]),
            "days_label": days_label(p["days_count"])
        })

    return templates.TemplateResponse(
        request=request,
        name="period_list.html",
        context={"periods": enriched, "min_days": min_days}
    )


@router.get("/period/{period_id}")
def get_period_detail(request: Request, period_id: int, show_next: bool = Query(False, alias="next")):
    published = [p for p in periods_db if p["status"] == "published"]

    if show_next:
        current_index = 0
        for i, p in enumerate(published):
            if p["id"] == period_id:
                current_index = i
                break
        period_id = published[(current_index + 1) % len(published)]["id"]

    period = None
    for p in published:
        if p["id"] == period_id:
            period = p
            break

    return templates.TemplateResponse(
        request=request,
        name="period_feed.html",
        context={
            "period": period,
            "likes_count": len(period["likes"]),
            "days_label": days_label(period["days_count"])
        }
    )


@router.get("/draft")
def get_draft(request: Request):
    draft = None
    for p in periods_db:
        if p["status"] == "draft":
            draft = p
            break

    return templates.TemplateResponse(
        request=request,
        name="period_draft.html",
        context={"period": draft}
    )
