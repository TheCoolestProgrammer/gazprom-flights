from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from src.database import create_db_and_tables, engine
from contextlib import asynccontextmanager
from src.routes import auth
from src.dependencies import get_current_user
from src.models import department, flight, passenger_flight, passenger, user
from sqladmin import Admin
from src.admin.admin_auth import admin_auth_backend
from src.admin.admin_views import (
    UserAdmin, DepartmentAdmin, FlightAdmin, 
    PassengerAdmin, PassengerFlightAdmin
)
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="gazprom kruto", lifespan=lifespan)
app.include_router(auth.router)

# Инициализация админки
admin = Admin(
    app, 
    engine, 
    authentication_backend=admin_auth_backend,
    title="Панель управления Газпром",
    base_url="/admin"
)

# Регистрация моделей в админке
admin.add_view(UserAdmin)
admin.add_view(DepartmentAdmin)
admin.add_view(FlightAdmin)
admin.add_view(PassengerAdmin)
admin.add_view(PassengerFlightAdmin)

@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def auth_exception_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url="/auth/login")

@app.get("/health_check")
def health_check():
    return {"status": "ok"}

# Ваш корневой роутер теперь может проверять куки
@app.get("/")
def home(request: Request, user = Depends(get_current_user)):
    return {"status": "authenticated", "message": "Добро пожаловать в систему"}