from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from app.schemas import PredictRequest, PredictResponse, EncodedImageResponse, EncodedImageRequest
from app.ml.model import MyModel
from fastapi.responses import HTMLResponse, JSONResponse
from app.core.config import settings
from app.logs import log

import logging
import requests
import base64
import io

model = MyModel()
router = APIRouter()

# ----------------------------------------------------------- Model routes ----------------------------------------------------------- #
from PIL import Image

@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
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
            cropped_images, boxes_and_classes = model.detect_and_collect_objects(model.object_detection_model, image, confidence_threshold=0.1)
            classified_objects = model.classify_objects(model.classification_model, cropped_images)
            annotated_image = model.annotate_image(image, boxes_and_classes, classified_objects)
            currencies = model.get_detected_counts(classified_objects, request.return_currency)
        except Exception as e:
            raise ValueError(f"Error in detecting and classifying objects - {str(e)}")
        
        # Convert annotated image to base64
        try:
            buffered = io.BytesIO()
            annotated_image.save(buffered, format="JPEG")
            annotated_image_base64 = base64.b64encode(buffered.getvalue()).decode()
        except Exception as e:
            raise ValueError(f"Error in encoding the image - {str(e)}")
        
        return PredictResponse(currencies=currencies, image=annotated_image_base64)
    
    except ValueError as e:
        log(f"Error in prediction - {str(e)}", logging.ERROR)
        raise HTTPException(status_code=500, detail=f"Internal error - {str(e)}")
    except Exception as e:
        log(f"General error - {str(e)}", logging.ERROR)
        raise HTTPException(status_code=500, detail=f"General error - {str(e)}")
    

@router.post("/encode_image" ,response_model=EncodedImageResponse)
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
async def show_image(request: EncodedImageRequest):
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
def get_exchange_rates():
    try:
        rates = exchange_service.get_exchange_rates()
        return {"exchange_rates": rates}
    except requests.RequestException as e:
        log(f"Error in fetching exchange rates - {str(e)}", logging.ERROR)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        log(f"General error - {str(e)}", logging.ERROR)
        raise HTTPException(status_code=500, detail=str(e))
    
# ----------------------------------------------------------- User routes ----------------------------------------------------------- #
from app.schemas import user as user_schemas
from app.db import db_api
from app.db.database import get_db
from sqlalchemy.orm import Session

@router.post("/users/register", response_model=user_schemas.User)
def create_user(user: user_schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db_api.get_user_by_email(db, email=user.email)
    if db_user: # If a user with the same email already exists
        log(f"Failed to create user - A user with the same email already exists!")
        raise HTTPException(status_code=400, detail="Email already registered")
    # If the user does not exist, create a new user and return it
    return db_api.create_user(db=db, user=user)