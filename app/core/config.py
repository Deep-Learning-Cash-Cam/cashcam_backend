from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CashCam"
    PROJECT_VERSION: str = "1.3"
    OBJECT_DETECTION_MODEL: str = "models/detection_model.pt"
    CLASSIFICATION_MODEL: str = "models/classification_model.pt"
    API_PREFIX: str = "/api"
    TEST_OUTPUT_PATH: str = "tests/test_output.txt"
    PORT: int = 80
    LOCAL_IP: str = "0.0.0.0"
    DEBUG: bool = True
    
    # Keys
    EXCHANGE_RATE_API_KEY: str

    model_config = ConfigDict(
        env_file = ".env",
        extra = "allow"
    )

settings = Settings()
