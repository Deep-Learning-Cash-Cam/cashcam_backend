from pydantic import BaseModel
from fastapi import UploadFile, File

class PredictRequest(BaseModel):
    image: str  # Base64 encoded image
    return_currency: str # The currency to return the value in, can be USD, EUR, or NIS only

    
class EncodedImageRequest(BaseModel):
    image: str  # Base64 encoded image