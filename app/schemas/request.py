from pydantic import BaseModel

class PredictRequest(BaseModel):
    image: str  # Base64 encoded image
    return_currency: str # The currency to return the value in, can be USD, EUR, or NIS only
