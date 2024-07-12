from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CahsCam"
    PROJECT_VERSION: str = "1.0.0"
    MODEL_PATH: str = "models/yolov8_model.pt" #TODO
    API_PREFIX: str = "/api"
    DEBUG: bool = True

    class Config:
        env_file = ".env"

settings = Settings()