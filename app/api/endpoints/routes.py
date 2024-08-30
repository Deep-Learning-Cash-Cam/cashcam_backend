from typing import Annotated
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.schemas import PredictRequest, PredictResponse, EncodedImageString, user_schemas
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

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[user_schemas.User | None, Depends(get_current_user)]

# ----------------------------------------------------------- Model routes ----------------------------------------------------------- #
from PIL import Image

# Predict an image and return the anotataed image with the detected counts
# If a user is logged in, save image to user's images, if not, save it to the general images
@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest, user: user_dependency, db: db_dependency):
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

        return PredictResponse(currencies= currencies, image= annotated_image_base64, image_id= None)
    except ValueError as e:
        log(f"Error in prediction - {str(e)}", logging.ERROR)
        raise HTTPException(status_code=400, detail=f"{str(e)}")
    except Exception as e:
        log(f"General error - {str(e)}", logging.CRITICAL)
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
            raise HTTPException(status_code=400, detail=str(e))
    else:
        raise HTTPException(status_code=404, detail="Not found")

@router.post("/show_image")
async def show_image(request: EncodedImageString):
    if settings.DEBUG:
        try:
            img_str = request.image
            decoded_img = base64.b64decode(img_str)
            
            html_content = f"""
            <html>
                <body>
                    <h1>Uploaded Image</h1>
                    <img src="data:image/jpeg;base64,{decoded_img}" />
                </body>
            </html>
            """
            return HTMLResponse(content=html_content, status_code=200)
        except Exception as e:
            log(f"Error in showing the image - {str(e)}", logging.ERROR)
            raise HTTPException(status_code=400, detail="Error in showing the image")
    else:
        raise HTTPException(status_code=404, detail="Not found")

# ----------------------------------------------------------- Exchange rates API routes ----------------------------------------------------------- #
from app.services.currency_exchange import exchange_service

@router.get("/exchange_rates")
def get_rates(user: user_dependency, db: db_dependency):
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

@router.post("/flag_image/{image_id}")
async def flag_image(user: user_dependency, db: db_dependency, image_id: str):
    if not user:
        raise HTTPException(status_code=401, detail="User not found - Unauthorized")
    try:
        # Flag the image
        if crud.flag_image(db, user.id, image_id):
            return {"message": "Image flagged successfully"}
        return {"message": "Image not found or already flagged"}
    except Exception as e:
        return {"message": "Error in flagging the image"}
    
@router.get("/get_images")
async def get_image_history(user: user_dependency, db: db_dependency):
    #Check if the user exists
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Get the user's image history
    try:
        images = crud.get_images_by_user_id(db, user.id)
        log(f"Got image history for user: {user.id}, logging.INFO", debug=True)
        return {"images": images}
    except Exception as e:
        log(f"Error in getting image history for user: {user.id} - {str(e)}", logging.ERROR)
        return {"message": "Error in getting image history"}
    