from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "寺院信息管理系统"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    DATABASE_URL: str = "sqlite+aiosqlite:///../database/temple.db"
    
    class Config:
        env_file = ".env"

settings = Settings()
