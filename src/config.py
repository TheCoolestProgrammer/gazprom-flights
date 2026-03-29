from pydantic import field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",extra='ignore')
    DB_NAME:str
    DB_USER:str
    DB_PASSWORD:str
    DB_PORT:int
    DB_HOST:str

    @computed_field
    @property
    def DATABASE_URL(self)->str:
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 20
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ADMIN_SECRET_KEY:str

config = Config()
