import os
from pydantic_settings import BaseSettings, SettingsConfigDict


env_file_path: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"
)


class AllSettings(BaseSettings):
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    DB_HOST: str = "postgres"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_APP_DB_NUM: int = 0
    REDIS_CELERY_NUM: int = 1

    S3_HOST: str = "s3"
    S3_PORT: int = 9000
    S3_ACCESS_KEY: str = "admin"
    S3_SECRET_KEY: str = "admin"
    BUCKET_NAME: str = "test_bucket"

    JWT_KEY: str = "test_key"
    JWT_ALGORITHM: str = "HS256"
    TOKEN_TYPE_FILED_NAME: str = "type"
    ACCESS_TOKEN_NAME: str = "access"
    REFRESH_TOKEN_NAME: str = "refresh"
    ACCESS_TOKEN_EXPIRES_MIN: int = 15
    REFRESH_TOKEN_EXPIRES_MIN: int = 44640

    APP_EMAIL: str
    APP_EMAIL_PASSWORD: str
    APP_HOST: str
    APP_PORT: int

    VIDEO_DURATION_CONSTRAINT: float = 16.0

    @property
    def s3_config_dict(self) -> dict:
        return {
            "endpoint_url": f"http://{self.S3_HOST}:{self.S3_PORT}",
            "access_key": self.S3_ACCESS_KEY,
            "secret_key": self.S3_SECRET_KEY,
            "bucket_name": self.BUCKET_NAME,
        }

    def redis_url(self, db_num: int) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{db_num}"

    model_config = SettingsConfigDict(
        env_file=env_file_path,
    )


all_settings = AllSettings()


class PostgresSettings:
    username: str = all_settings.DB_USER
    password: str = all_settings.DB_PASS
    host: str = all_settings.DB_HOST
    port: str = all_settings.DB_PORT
    db_name: str = all_settings.DB_NAME

    url: str = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{db_name}"


class RedisSettings:
    host: str = all_settings.REDIS_HOST
    port: str = all_settings.REDIS_PORT
    app_db_num: int = all_settings.REDIS_APP_DB_NUM
    celery_num: int = all_settings.REDIS_CELERY_NUM

    app_url: str = all_settings.redis_url(app_db_num)
    broker_url: str = all_settings.redis_url(celery_num)


class S3Settings:
    host: str = all_settings.S3_HOST
    port: int = all_settings.S3_PORT
    access_key: str = all_settings.S3_ACCESS_KEY
    secret_key: str = all_settings.S3_SECRET_KEY
    bucket_name: str = all_settings.BUCKET_NAME
    config_dict: dict = all_settings.s3_config_dict


class AuthSettings:
    jwt_key: str = all_settings.JWT_KEY
    jwt_algorithm: str = all_settings.JWT_ALGORITHM
    token_type_filed_name: str = all_settings.TOKEN_TYPE_FILED_NAME
    access_token_name: str = all_settings.ACCESS_TOKEN_NAME
    refresh_token_name: str = all_settings.REFRESH_TOKEN_NAME
    access_token_expires_min: int = all_settings.ACCESS_TOKEN_EXPIRES_MIN
    refresh_token_expires_min: int = all_settings.REFRESH_TOKEN_EXPIRES_MIN


class EmailClientSettings:
    email: str = all_settings.APP_EMAIL
    password: str = all_settings.APP_EMAIL_PASSWORD


class AppSettings:
    video_duration_constraint: float = all_settings.VIDEO_DURATION_CONSTRAINT
    host: str = all_settings.APP_HOST
    port: int = all_settings.APP_PORT
    verification_code_ttl_seconds: int = 600


class Settings:
    postgres = PostgresSettings()
    redis = RedisSettings()
    s3 = S3Settings()
    auth = AuthSettings()
    email_client = EmailClientSettings()
    app = AppSettings()


settings = Settings()
