from pydantic import BaseModel
from src.models.user import Role

class UserLogin(BaseModel):
    login: str
    password: str


class UserRegister(BaseModel):
    login: str
    password: str
    name: str
    department_id:int
    role: Role

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    user_id: int = None
    login: str = None
