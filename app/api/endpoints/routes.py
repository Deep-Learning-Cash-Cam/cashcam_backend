from typing import Annotated
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from app.api.dependencies import get_current_user_by_token, get_current_user_or_None
from app.db.database import get_db
from app.schemas import PredictRequest, PredictResponse, EncodedImageResponse, EncodedImageString, user_schemas
from app.ml.model import MyModel
from fastapi.responses import HTMLResponse, JSONResponse
from app.core.config import settings
from app.logs import log
from app.db import crud

import logging
from requests import Session, RequestException
import base64
import io

model = MyModel()
router = APIRouter()

db_dependancy = Annotated[Session, Depends(get_db)]
user_dependancy = Annotated[user_schemas.User | None, Depends(get_current_user_or_None)]

# ----------------------------------------------------------- Model routes ----------------------------------------------------------- #
from PIL import Image

# Predict an image and return the anotataed image with the detected counts
# If a user is logged in, save image to user's images, if not, save it to the general images
@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest, user: user_dependancy, db: db_dependancy):
    try:
        # Check that return currency is valid
        if request.return_currency not in exchange_service.CURRENCIES:
            if request.return_currency == "NIS":
                request.return_currency = "ILS"
            else:
                raise ValueError("Invalid return currency")
        try:
            # Decode base64 image
            image_data = base64.b64decode(request.image)
            image = Image.open(io.BytesIO(image_data))
            image = image.convert('RGB')
        except Exception as e:
            raise ValueError("Invalid image - Unable to decode the image")
        
        # Detect, classify objects, anotate image and get the detected counts with the requested currency's conversion rate
        try:
            annotated_image , currencies = model.predict_image(image, request.return_currency)
        except Exception as e:
            raise ValueError(f"Could not predict the image. Please try again later.")
        
        # Convert annotated image to base64
        try:
            buffered = io.BytesIO()
            annotated_image.save(buffered, format="JPEG")
            annotated_image_base64 = base64.b64encode(buffered.getvalue()).decode()
        except Exception as e:
            raise ValueError(f"Error in encoding the image - {str(e)}")
        
        # Save the image to the user's images
        try:
            if user:
                user_id = user.id
                image_id = crud.save_image(db, annotated_image_base64, user_id)
                return PredictResponse(currencies= currencies, image= annotated_image_base64, image_id= image_id)
        except Exception as e:
            log(f"Error in saving the image - {str(e)}", logging.ERROR)
            raise HTTPException(status_code=500, detail=f"Internal error - {str(e)}")
    
    except ValueError as e:
        log(f"Error in prediction - {str(e)}", logging.ERROR)
        raise HTTPException(status_code=500, detail=f"Internal error - {str(e)}")
    except Exception as e:
        log(f"General error - {str(e)}", logging.ERROR)
        raise HTTPException(status_code=500, detail=f"General error - {str(e)}")
    

@router.post("/encode_image" ,response_model= EncodedImageString)
async def upload_image(file: UploadFile = File(...)):
    if settings.DEBUG:
        try:
            # Read the image
            image = Image.open(io.BytesIO(await file.read()))
            
            # Convert the image to RGB and encode it to base64
            image = image.convert("RGB")
            Buffered = io.BytesIO()
            image.save(Buffered, format="JPEG")
            img_str = base64.b64encode(Buffered.getvalue()).decode()
            return JSONResponse(content={"image": img_str}, status_code=200)
        except Exception as e:
            log(f"Error in encoding the image - {str(e)}", logging.ERROR)
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=404, detail="This route is only available in debug mode")

@router.post("/show_image")
async def show_image(request: EncodedImageString):
    if settings.DEBUG:
        try:
            img_str = request.image
            
            html_content = f"""
            <html>
                <body>
                    <h1>Uploaded Image</h1>
                    <img src="data:image/jpeg;base64,{img_str}" />
                </body>
            </html>
            """
            return HTMLResponse(content=html_content, status_code=200)
        except Exception as e:
            log(f"Error in showing the image - {str(e)}", logging.ERROR)
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=404, detail="This route is only available in debug mode")

# ----------------------------------------------------------- Exchange rates API routes ----------------------------------------------------------- #
from app.services.currency_exchange import exchange_service

@router.get("/exchange_rates")
def get_exchange_rates(user: user_dependancy, db: db_dependancy):
    try:
        # Only allow admin users to access the exchange rates
        if user and user.role == "admin":
            rates = exchange_service.get_exchange_rates()
            return {"exchange_rates": rates}

        raise HTTPException(status_code=401, detail="Unauthorized")
    except RequestException as e:
        log(f"Error in fetching exchange rates - {str(e)}", logging.ERROR)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        log(f"General error - {str(e)}", logging.ERROR)
        raise HTTPException(status_code=500, detail=str(e))
    
# ----------------------------------------------------------- User routes ----------------------------------------------------------- #

#TODO: ADD FLAG IMAGE ROUTE
@router.post("/flag_image/{image_id}")
async def flag_image(user: user_dependancy, db: db_dependancy, image_id: int):
    if not user:
        raise HTTPException(status_code=401, detail="User not found - Unauthorized")
    try:
        # Flag the image
        if crud.flag_image(db, user.id, image_id):
            return {"message": "Image flagged successfully"}
        return {"message": "Image not found or already flagged"}
    except Exception as e:
        return {"message": "Error in flagging the image"}