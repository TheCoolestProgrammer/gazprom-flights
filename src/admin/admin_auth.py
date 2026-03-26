from sqladmin.authentication import AuthenticationBackend
from fastapi import Request
from src.security import verify_token, create_tokens, verify_password
from src.models.user import User, Role

from src.database import engine
from sqlalchemy.orm import Session

class AdminAuth(AuthenticationBackend):
    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("access_token") or request.cookies.get("access_token")
        if not token:
            return False

        payload = verify_token(token.replace("Bearer ", ""))
        if not payload:
            return False

        # Открываем сессию вручную прямо здесь
        with Session(engine) as session:
            user_id = payload.get("user_id")
            user = session.query(User).filter(User.id == user_id).first()
            return user is not None and user.role == Role.ADMIN

    async def login(self, request: Request) -> bool:
        form = await request.form()
        login_val = form.get("username")
        password_val = form.get("password")

        with Session(engine) as session:
            user = session.query(User).filter(User.login == login_val).first()
            if user and verify_password(password_val, user.password_hash) and user.role == Role.ADMIN:
                tokens = create_tokens(user_id=user.id, login=user.login)
                request.session.update({"access_token": f"Bearer {tokens["access_token"]}"})
                return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    

# Инициализируем секретный ключ для сессий админки
admin_auth_backend = AdminAuth(secret_key="SUPER_SECRET_KEY_FOR_ADMIN")