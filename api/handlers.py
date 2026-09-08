from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from data.collections import (
    forecasts_db,
    historical_revenue_quarterly,
    historical_revenue_monthly,
    historical_revenue_yearly,
)

router = APIRouter()
# Указываем, где искать HTML файлы
templates = Jinja2Templates(directory="templates")

HISTORY_BY_UNIT = {
    "month": historical_revenue_monthly,
    "quarter": historical_revenue_quarterly,
    "year": historical_revenue_yearly,
}

# Во сколько раз домножить среднее по window_unit, чтобы получить оценку для period_type цели
MULTIPLIER = {
    ("year", "quarter"): 4,
    ("year", "month"): 12,
    ("quarter", "month"): 3,
}


def calculate_forecast(target_period: str, window_count: int | None, window_unit: str | None, period_type: str) -> float | None:
    """
    Рассчитывает прогноз методом скользящей средней.
    window_count — сколько периодов взять, window_unit — периодов какого типа (month/quarter/year).
    period_type — тип самого прогнозируемого периода (нужен только для домножения, если типы не совпадают).
    """
    if window_count is None or window_unit is None:
        return None

    history = HISTORY_BY_UNIT[window_unit]
    periods_order = list(history.keys())

    if target_period in periods_order:
        target_index = periods_order.index(target_period)
    else:
        target_index = len(periods_order)

    start = max(0, target_index - window_count)
    prior_periods = periods_order[start:target_index]

    if not prior_periods:
        return None

    values = [history[p] for p in prior_periods]
    average = sum(values) / len(values)

    multiplier = MULTIPLIER.get((period_type, window_unit), 1)
    return round(average * multiplier, 2)


@router.get("/")
def get_catalog(request: Request, min_revenue: str = None):

    parsed_min_revenue = None
    if min_revenue:
        try:
            parsed_min_revenue = float(min_revenue.replace(",", "."))
        except ValueError:
            parsed_min_revenue = None

    published = [f for f in forecasts_db if f["status"] == "published"]

    enriched = []
    for f in published:
        predicted = calculate_forecast(f["target_period"], f["window_count"], f["window_unit"], f["period_type"])
        if parsed_min_revenue is not None and (predicted is None or predicted < parsed_min_revenue):
            continue
        enriched.append({
            **f,
            "predicted_revenue": predicted,
            "likes_count": len(f["likes"])
        })

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"forecasts": enriched, "min_revenue": min_revenue}
    )


@router.get("/forecast/{forecast_id}")
def get_forecast_detail(request: Request, forecast_id: int, show_next: bool = Query(False, alias="next")):
    published = [f for f in forecasts_db if f["status"] == "published"]

    if show_next:
        current_index = 0
        for i, f in enumerate(published):
            if f["id"] == forecast_id:
                current_index = i
                break
        forecast_id = published[(current_index + 1) % len(published)]["id"]

    forecast = None
    for f in published:
        if f["id"] == forecast_id:
            forecast = f
            break

    predicted = calculate_forecast(forecast["target_period"], forecast["window_count"], forecast["window_unit"], forecast["period_type"])

    return templates.TemplateResponse(
        request=request,
        name="feed.html",
        context={
            "forecast": forecast,
            "predicted_revenue": predicted,
            "likes_count": len(forecast["likes"])
        }
    )


@router.get("/draft")
def get_draft(request: Request):
    draft = None
    for f in forecasts_db:
        if f["status"] == "draft":
            draft = f
            break

    predicted = calculate_forecast(draft["target_period"], draft["window_count"], draft["window_unit"], draft["period_type"])

    return templates.TemplateResponse(
        request=request,
        name="draft.html",
        context={"forecast": draft, "predicted_revenue": predicted}
    )
