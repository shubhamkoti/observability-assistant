from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://ecuser:ecsecret@localhost:5432/ecommerce"
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "ecommerce_logs"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    low_stock_threshold_default: int = 10
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/%2F"
    rabbitmq_queue_name: str = "email_jobs"
    email_from_address: str = "no-reply@marketgrid.local"


settings = Settings()
