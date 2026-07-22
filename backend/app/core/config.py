from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Application
    app_env: str = "production"
    app_name: str = "ZauriScore"
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"

    # Security
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    # S3 Storage
    s3_endpoint_url: Optional[str] = None
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_bucket_name: str = "zauriscore-reports"
    s3_region: str = "us-east-1"

    # Blockchain APIs
    etherscan_api_key: str
    polygonscan_api_key: str = ""
    arbiscan_api_key: str = ""
    basescan_api_key: str = ""

    # Stripe
    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_pro_price_id: str = ""
    stripe_enterprise_price_id: str = ""

    # Rate Limiting
    rate_limit_free_scans_per_day: int = 5
    rate_limit_pro_scans_per_day: int = 100

    # Analysis
    slither_timeout: int = 120
    solc_path: str = "/usr/local/bin/solc"
    max_contract_size_kb: int = 500

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
