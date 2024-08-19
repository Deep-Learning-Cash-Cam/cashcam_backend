from pydantic_settings import BaseSettings
from datetime import datetime, timedelta, timezone

utc3_time = timezone(timedelta(hours=3))

class Settings(BaseSettings):
    # Global settings
    PROJECT_NAME: str = "CashCam"
    PROJECT_VERSION: str = "1.0.0"
    OBJECT_DETECTION_MODEL: str = "models/bill_coin_yolo_best.pt"
    CLASSIFICATION_MODEL: str = "models/class_YOLO_model_best.pt"
    API_PREFIX: str = "/api"
    TEST_OUTPUT_PATH: str = "tests/test_output.txt"
    LOCAL_IP: str = "0.0.0.0"
    DATABASE_URL: str = "sqlite:///./sql_app.db" #TODO: Update the database URL (currently dumps to root dir), postgres maybe?
    PORT: int = 80
    DEBUG: bool = True
    
    # JWT
    JWT_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15 # Used by JWT to check if the token is expired
    JWT_ALGORITHM: str = "HS256"
    
    # Google OAuth2
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    
    # Exchange rate API
    EXCHANGE_RATE_API_KEY: str
    UPDATE_RATES_INTERVAL_HOURS: int = 24 # Exchange rate service interval in hours
    
    # Time
    @property
    def TIME_NOW(self):
        return datetime.now(utc3_time)

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
