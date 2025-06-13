import os
from pydantic_settings import BaseSettings, SettingsConfigDict


env_file_path: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    ".env"
)


class Settings(BaseSettings):
    DB_USERNAME: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str

    @property
    def asyncpg_db_url(self) -> str:
        return f"postgresql+psycopg://{self.DB_USERNAME}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=env_file_path,
    )


settings = Settings()
