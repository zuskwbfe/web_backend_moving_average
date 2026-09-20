# Коллекция периодов (услуг) — месяцы и кварталы.
# Карточки не содержат расчётов, только атрибуты самого периода (порядок, количество дней).

periods_db = [
    {
        "id": 1,
        "title": "Октябрь",
        "order": 10,
        "days_count": 31,
        "description": "Отчётный период — октябрь 2026 года. Десятый месяц календарного года, относится к четвёртому кварталу. В этом периоде 31 день, что делает его одним из семи самых продолжительных месяцев года. Октябрь завершает осенний сезон и открывает подготовку к итогам года.",
        "status": "published",
        "image_url": "http://localhost:9000/forecasts/forecast_oct_2026.png",
        "video_url": "http://localhost:9000/forecasts/forecast_oct_2026.mp4",
        "likes": [1, 2, 3, 4, 5]
    },
    {
        "id": 2,
        "title": "3 квартал",
        "order": 3,
        "days_count": 92,
        "description": "Отчётный период — 3 квартал 2026 года, включающий июль, август и сентябрь. Это третий из четырёх кварталов календарного года, продолжительностью 92 дня. Традиционно считается переходным периодом между летним и осенним сезонами, часто отличается неравномерной активностью по месяцам.",
        "status": "published",
        "image_url": "http://localhost:9000/forecasts/forecast_q3_2026.png",
        "video_url": "http://localhost:9000/forecasts/forecast_q3_2026.mp4",
        "likes": [1, 2, 5]
    },
    {
        "id": 3,
        "title": "2 квартал",
        "order": 2,
        "days_count": 91,
        "description": "Отчётный период — 2 квартал 2026 года, включающий апрель, май и июнь. Второй квартал календарного года продолжительностью 91 день. Завершает первое полугодие и традиционно предшествует началу летнего сезона, охватывая переходный весенне-летний период.",
        "status": "published",
        "image_url": "http://localhost:9000/forecasts/forecast_q2_2026.jpg",
        "video_url": "http://localhost:9000/forecasts/forecast_q2_2026.mp4",
        "likes": [1, 2, 3, 7, 8, 11]
    },
    {
        "id": 4,
        "title": "4 квартал",
        "order": 4,
        "days_count": 92,
        "description": "Черновик периода. Данные ещё уточняются.",
        "status": "draft",
        "image_url": "http://localhost:9000/forecasts/forecast_q4_2026.png",
        "video_url": "http://localhost:9000/forecasts/forecast_q4_2026.mp4",
        "likes": []
    },
    {
        "id": 5,
        "title": "Июль",
        "order": 7,
        "days_count": 31,
        "description": "Период, признанный неактуальным и удалённым из каталога.",
        "status": "deleted",
        "image_url": "http://localhost:9000/forecasts/forecast_jul_2026.png",
        "video_url": "http://localhost:9000/forecasts/forecast_jul_2026.mp4",
        "likes": [1, 3, 7, 8, 12]
    },
]
