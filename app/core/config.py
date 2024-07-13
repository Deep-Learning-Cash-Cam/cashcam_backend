from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CahsCam"
    PROJECT_VERSION: str = "1.0.0"
    MODEL_PATH: str = "models/yolov8_model.pt" #TODO
    IMAGE_BASE_URL: str = "https://www.example.com/images" #TODO
    API_PREFIX: str = "/api"
    TEST_OUTPUT_PATH: str = "tests/test_output.txt"
    DEBUG: bool = True

    class ConfigDict:
        env_file = ".env"

settings = Settings()