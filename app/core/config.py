from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CahsCam"
    PROJECT_VERSION: str = "1.0.0"
    OBJECT_DETECTION_MODEL: str = "models/bill_coin_yolo_best.pt"
    CLASSIFICATION_MODEL: str = "models/class_YOLO_model_best.pt"
    IMAGE_BASE_URL: str = "https://www.example.com/images" #TODO
    API_PREFIX: str = "/api"
    TEST_OUTPUT_PATH: str = "tests/test_output.txt"
    PORT: int = 80
    LOCAL_IP: str = "0.0.0.0"
    DEBUG: bool = True

    class ConfigDict:
        env_file = ".env"

settings = Settings()
