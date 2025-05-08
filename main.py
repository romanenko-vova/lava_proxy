"""FastAPI proxy: Lava webhook ⇒ SaleBot webhook

- Exposes POST /payment for new API
- Exposes POST /regular_pay for recurring payments
- Extracts utm_source (api), buyer.email (clientId) and builds message
- Forwards original body to SaleBot as JSON plus required query params
- Uses httpx.AsyncClient
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import init_db
from routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Обработчик жизненного цикла приложения."""
    # Код, выполняемый при запуске приложения
    await init_db()
    yield
    # Код, выполняемый при завершении приложения
    print("Shutting down application")


# Создаем экземпляр FastAPI с использованием lifespan
app = FastAPI(
    title="Lava → SaleBot proxy", 
    version="1.0.0",
    lifespan=lifespan
)

# Добавляем маршруты из routes.py
app.include_router(router) 