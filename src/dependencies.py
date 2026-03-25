from fastapi import Request, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from src.database import SessionDep
from src.models.user import User
from src.security import verify_token

async def get_current_user(request: Request, session: SessionDep):
    # Достаем куку
    token_cookie = request.cookies.get("access_token")
    
    # Если куки нет вообще
    if not token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован"
        )

    # Убираем префикс "Bearer ", если ты его сохранял с ним
    token = token_cookie.replace("Bearer ", "") if token_cookie.startswith("Bearer ") else token_cookie

    # Проверяем токен (используем твою функцию из security)
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия истекла или токен невалиден"
        )

    user_id: int = payload.get("user_id")
    user = session.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
        
    return user