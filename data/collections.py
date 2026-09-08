# Реальные данные о выручке ПАО "Группа Русагро" (млрд руб., до межсегментных элиминаций)
# Источник: официальные операционные результаты компании (rusagrogroup.ru)

historical_revenue_quarterly = {
    "1 квартал 2025": 81.98,
    "2 квартал 2025": 88.27,
    "3 квартал 2025": 96.79,
    "4 квартал 2025": 156.75,
    "1 квартал 2026": 84.119,
    "2 квартал 2026": 107.0,
}

# Помесячные данные получены интерполяцией: квартальное значение разделено поровну на 3 месяца.
historical_revenue_monthly = {
    "Январь 2025": 27.327, "Февраль 2025": 27.327, "Март 2025": 27.327,
    "Апрель 2025": 29.423, "Май 2025": 29.423, "Июнь 2025": 29.423,
    "Июль 2025": 32.263, "Август 2025": 32.263, "Сентябрь 2025": 32.263,
    "Октябрь 2025": 52.25, "Ноябрь 2025": 52.25, "Декабрь 2025": 52.25,
    "Январь 2026": 28.04, "Февраль 2026": 28.04, "Март 2026": 28.04,
    "Апрель 2026": 35.667, "Май 2026": 35.667, "Июнь 2026": 35.667,
}

historical_revenue_yearly = {
    "2025 год": 423.79,
}

forecasts_db = [
    {
        "id": 1,
        "title": "Прогноз выручки: Октябрь 2026",
        "target_period": "Октябрь 2026",
        "period_type": "month",
        "window_count": 3,
        "window_unit": "month",
        "description": "Прогноз выручки на октябрь 2026 рассчитан методом скользящей средней по 3 предыдущим месяцам (интерполированы из квартальных отчётов, т.к. помесячные данные компанией не публикуются).",
        "status": "published",
        "image_url": "http://localhost:9000/forecasts/forecast_oct_2026.png",
        "video_url": "http://localhost:9000/forecasts/forecast_oct_2026.mp4",
        "likes": [1, 2, 3, 4, 5]
    },
    {
        "id": 2,
        "title": "Прогноз выручки: 3 квартал 2026",
        "target_period": "3 квартал 2026",
        "period_type": "quarter",
        "window_count": 3,
        "window_unit": "quarter",
        "description": "Прогноз выручки на 3 квартал 2026 рассчитан методом скользящей средней по 3 предыдущим кварталам. Модель использует фактическую выручку группы 'Русагро' и сглаживает сезонные колебания.",
        "status": "published",
        "image_url": "http://localhost:9000/forecasts/forecast_q3_2026.png",
        "video_url": "http://localhost:9000/forecasts/forecast_q3_2026.mp4",
        "likes": [1, 2, 5]
    },
    {
        "id": 3,
        "title": "Прогноз выручки: 2026 год",
        "target_period": "2026 год",
        "period_type": "year",
        "window_count": 6,
        "window_unit": "quarter",
        "description": "Годовой прогноз выручки группы 'Русагро' на 2026 год рассчитан методом скользящей средней по 6 известным кварталам, что обеспечивает сглаженную оценку долгосрочного тренда.",
        "status": "published",
        "image_url": "http://localhost:9000/forecasts/forecast_year_2026.png",
        "video_url": "http://localhost:9000/forecasts/forecast_year_2026.mp4",
        "likes": [1, 2, 3, 7, 8, 11]
    },
    {
        "id": 4,
        "title": "Прогноз выручки: 4 квартал 2026",
        "target_period": "4 квартал 2026",
        "period_type": "quarter",
        "window_count": None,
        "window_unit": None,
        "description": "Черновик прогноза. Окно расчёта ещё не выбрано.",
        "status": "draft",
        "image_url": "http://localhost:9000/forecasts/forecast_q4_2026.png",
        "video_url": "http://localhost:9000/forecasts/forecast_q4_2026.mp4",
        "likes": []
    },
    {
        "id": 5,
        "title": "Прогноз выручки: Июль 2026",
        "target_period": "Июль 2026",
        "period_type": "month",
        "window_count": 3,
        "window_unit": "month",
        "description": "Прогноз, признанный неактуальным после пересмотра модели расчёта.",
        "status": "deleted",
        "image_url": "http://localhost:9000/forecasts/forecast_jul_2026.png",
        "video_url": "http://localhost:9000/forecasts/forecast_jul_2026.mp4",
        "likes": [1, 3, 7, 8, 12]
    },
]
