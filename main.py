from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from src.database import create_db_and_tables, engine
from contextlib import asynccontextmanager
from src.routes import auth, transport_dispatcher, department_director, dispatcher, main_dispatcher
from src.dependencies import get_current_user
from src.models import department, passenger, flights, passenger_flight, user
from sqladmin import Admin
from src.admin.admin_auth import admin_auth_backend
from src.admin.admin_views import (
    UserAdmin, DepartmentAdmin, 
    PassengerAdmin, PassengerFlightAdmin, FlightsAdmin
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

templates = Jinja2Templates(directory="templates")

app = FastAPI(title="gazprom kruto", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(transport_dispatcher.router)
app.include_router(department_director.router)
app.include_router(dispatcher.router)
app.include_router(main_dispatcher.router)
# Инициализация админки
admin = Admin(
    app, 
    engine, 
    authentication_backend=admin_auth_backend,
    title="Панель управления авиаперевозками",
    base_url="/admin"
)

# Регистрация моделей в админке
admin.add_view(UserAdmin)
admin.add_view(DepartmentAdmin)
admin.add_view(PassengerAdmin)
admin.add_view(PassengerFlightAdmin)
admin.add_view(FlightsAdmin)

@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def auth_exception_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url="/auth/login")

@app.exception_handler(status.HTTP_403_FORBIDDEN)
async def role_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        request=request, 
        name="errors/error.html", 
        context={
        "message": "FORBIDEN!!!! вам сюда нельзя!!!",
    })

@app.exception_handler(status.HTTP_204_NO_CONTENT)
async def content_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        request=request, 
        name="errors/error.html", 
        context={
        "message": "no content",
    })

@app.get("/health_check")
def health_check():
    return {"status": "ok"}

# Ваш корневой роутер теперь может проверять куки
@app.get("/")
def home(request: Request, userdb = Depends(get_current_user)):
    redirection_table = user.Role.REDIRECTION_TABLE()
    if userdb.role in redirection_table:
        return RedirectResponse(redirection_table[userdb.role])
    else:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
