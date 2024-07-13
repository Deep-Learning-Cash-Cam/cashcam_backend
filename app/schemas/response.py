from pydantic import BaseModel
from typing import Dict

# CurrencyInfo is the info sent to the user about a specific currency that was detected in the image
class CurrencyInfo(BaseModel):
    quantity: int  # How many objects of this currency were detected in the image
    return_currency_value: float # The value of one object of this currency and it's value in the return currency
    
# PredictResponse is the response sent to a predict request containing the detected currencies and their values 
# along with the image url with the YOLO detection boxes
class PredictResponse(BaseModel):
    currencies: Dict[str, CurrencyInfo]
    image: str # Base64 encoded image