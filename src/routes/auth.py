from fastapi import APIRouter, Form, HTTPException, Request, Response, status
from fastapi.params import Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database import SessionDep
from src.models.user import Role, User
from src.schemas.auth import TokenRefresh, UserLogin, UserRegister, Token
from src.schemas.user import UserResponse
from src.security import (
    verify_password,
    get_password_hash,
    create_tokens,
    verify_token,
)
from src.config import config
from src.templates_config import templates

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # Проверяем, есть ли уже токен
    token = request.cookies.get("access_token")
    if token:
        # Пытаемся его проверить, чтобы не редиректить по битому токену
        payload = verify_token(token.replace("Bearer ", ""))
        if payload:
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(request=request, name="login.html")
# @router.get("/login", response_class=HTMLResponse)
# async def login_page(request: Request, session: SessionDep):
#     # Если пользователь уже авторизован (проверяем access_token в cookie), редиректим на дашборд
#     access_token = request.cookies.get("access_token")
#     if access_token:
#         payload = verify_token(access_token, is_refresh=False)
#         if payload:
#             user_id = payload.get("user_id")
#             user = session.query(User).filter(User.id == user_id).first()
#             if user:
#                 return RedirectResponse(url="/dashboard", status_code=303)
#     return templates.TemplateResponse("login.html", {"request": request})

@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, session: SessionDep):
    existing_user = session.query(User).filter(User.login == user_data.login).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Login already registered"
        )

    hashed_password = get_password_hash(user_data.password)
    user = User(
        login=user_data.login,
        password_hash=hashed_password,
        name=user_data.name,
        department_id=user_data.department_id,
        role=user_data.role
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


# @router.post("/login", response_model=Token)
# def login(response: Response, user_data: UserLogin, session: SessionDep):
#     user = session.query(User).filter(User.login == user_data.login).first()
#     if not user or not verify_password(user_data.password, user.password_hash):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect login or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     # Создаем пару токенов
#     tokens = create_tokens(user_id=user.id, login=user.login)

#     return tokens
@router.post("/login")
def login(
    request: Request,
    session: SessionDep,
    login: str = Form(...),
    password: str = Form(...)
):
    user = session.query(User).filter(User.login == login).first()
    if not user or not verify_password(password, user.password_hash):
        # В случае ошибки можно вернуть ту же страницу с текстом ошибки
        return templates.TemplateResponse(
            request=request, 
            name="login.html", 
            context={"error": "Неверный логин или пароль"}
        )
    tokens = create_tokens(user_id=user.id, login=user.login)

    # Создаем редирект на главную
    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    # Устанавливаем куки
    redirect.set_cookie(
        key="access_token", 
        value=f"Bearer {tokens["access_token"]}", 
        httponly=True,
        max_age=60*config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    redirect.set_cookie(
        key="refresh_token", 
        value=tokens["refresh_token"], 
        httponly=True,
        max_age=86400 * config.REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    return redirect

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    # Удаляем обе куки
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return response

@router.post("/refresh", response_model=Token)
def refresh_token(token_data: TokenRefresh, session: SessionDep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Проверяем refresh токен
    payload = verify_token(token_data.refresh_token, is_refresh=True)
    if payload is None:
        raise credentials_exception

    user_id: int = payload.get("user_id")
    login: str = payload.get("login")

    if user_id is None or login is None:
        raise credentials_exception

    # Проверяем, существует ли пользователь
    user = session.query(User).filter(User.id == user_id, User.login == login).first()
    if user is None:
        raise credentials_exception

    # Создаем новую пару токенов
    tokens = create_tokens(user_id=user.id, login=user.login)

    return tokens
