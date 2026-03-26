from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from src.config import config
from src.database import create_db_and_tables, SessionDep
from contextlib import asynccontextmanager
from src.routes import auth
from src.dependencies import get_current_user
from src.models import department, flight, passenger_flight, passenger, user

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="gazprom kruto", lifespan=lifespan)
app.include_router(auth.router)

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