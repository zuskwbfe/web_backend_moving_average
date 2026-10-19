from fastapi import FastAPI
import uvicorn
from fastapi.staticfiles import StaticFiles

from api.handlers import router as pages_router
from api.periods import router as periods_router
from api.users import router as users_router

app = FastAPI(
    title="Periods Catalog API",
    description=(
        "Каталог отчётных периодов. Чтение доступно гостю. Методы создателя требуют сессии: "
        "сначала выполните POST /api/users/login."
    ),
    openapi_tags=[
        {"name": "periods", "description": "Периоды: чтение для всех, изменение для создателя"},
        {"name": "users", "description": "Регистрация, вход и выход"},
    ],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages_router, include_in_schema=False)
app.include_router(periods_router)
app.include_router(users_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
