from fastapi import APIRouter, HTTPException
from app.schemas.request import PredictRequest
from app.schemas.response import PredictResponse
from app.ml.model import model #TODO: Implement this function
from app.core.config import settings
import base64
import uuid

router = APIRouter()

@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    try:
        # Decode the base64 image
        image_data = base64.b64decode(request.image)
        
        # Predict currencies in the image with the model
        image, currencies = model.predict(image_data, request.return_currency) #TODO: Implement this function
        
        # Optional: Encode the image to base64 here instead of in the model
        
        # Prepare the response
        response = PredictResponse(
            currencies=currencies,
            image=image
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
