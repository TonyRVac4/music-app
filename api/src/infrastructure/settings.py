import os
from pydantic_settings import BaseSettings, SettingsConfigDict

env_file_path: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"
)


class PostgresSettings(BaseSettings):
    username: str = "postgres"
    password: str = "postgres"
    host: str = "postgres"
    port: int = 5432
    db_name: str = "postgres"

    url: str = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{db_name}"


class RedisSettings(BaseSettings):
    host: str = "redis"
    port: int = 6379
    app_db_num: int = 0
    celery_broker_num: int = 1

    app_url: str = f"redis://{host}:{port}/{app_db_num}"
    broker_url: str = f"redis://{host}:{port}/{celery_broker_num}"


class S3Settings(BaseSettings):
    host: str = "s3"
    port: int = 9000
    access_key: str = "admin"
    secret_key: str = "admin"
    bucket_name: str = "test_bucket"
    http_prefix: str = "http"

    @property
    def config_dict(self) -> dict:
        return {
            "endpoint_url": f"{self.http_prefix}://{self.host}:{self.port}",
            "access_key": self.access_key,
            "secret_key": self.secret_key,
            "bucket_name": self.buket_name,
        }


class AuthSettings(BaseSettings):
    jwt_key: str = "test_key"
    jwt_algorithm: str = "HS256"
    token_type_filed_name: str = "type"
    access_token_name: str = "access"
    refresh_token_name: str = "refresh"
    access_token_expires_min: int = 15
    refresh_token_expires_min: int = 44640


class EmailClientSettings(BaseSettings):
    email: str = "example@gmail.com"
    password: str = "password"
    verification_code_ttl_seconds: int = 600


class AppSettings(BaseSettings):
    host: str = "localhost"
    port: int = "8341"


class YouTubeSettings(BaseSettings):
    video_duration_constraint: float = 16.0
    api_key: str = "Some API key"
    visitor_info1_live: str = "Some visitor key"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="API__",
        env_file=(env_file_path, ".env", ".env.local"),
        env_file_encoding="utf-8",
        # разделитель для вложенных значений
        env_nested_delimiter="__",
        # если значение есть берет из env если нет будет использовано значение по умолчанию
        nested_model_default_partial_update=True,
    )

    postgres: PostgresSettings = PostgresSettings()
    redis: RedisSettings = RedisSettings()
    s3: S3Settings = S3Settings()
    auth: AuthSettings = AuthSettings()
    email_client: EmailClientSettings = EmailClientSettings()
    app: AppSettings = AppSettings()
    youtube: YouTubeSettings = YouTubeSettings()


settings = Settings()
