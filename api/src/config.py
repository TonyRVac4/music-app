import os
from pydantic_settings import BaseSettings, SettingsConfigDict


env_file_path: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    ".env"
)


class Settings(BaseSettings):
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB_NUM: int
    JWT_KEY: str
    JWT_ALGORITHM: str
    TOKEN_TYPE_FILED_NAME: str
    ACCESS_TOKEN_NAME: str
    REFRESH_TOKEN_NAME: str
    ACCESS_TOKEN_EXPIRES_MIN: int
    REFRESH_TOKEN_EXPIRES_MIN: int
    APP_EMAIL: str
    APP_EMAIL_PASSWORD: str
    APP_HOST: str
    APP_PORT: int

    @property
    def asyncpg_db_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def redis_db_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB_NUM}?decode_responses=True"

    model_config = SettingsConfigDict(
        env_file=env_file_path,
    )


settings = Settings()
