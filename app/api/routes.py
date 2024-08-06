from fastapi import APIRouter, HTTPException
from app.schemas import PredictRequest, PredictResponse, CurrencyInfo
from app.ml.model import MyModel
import base64
from PIL import Image
import io
import numpy as np
from ultralytics import YOLO
import cv2

router = APIRouter()
model = MyModel()
debug = False

@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    if debug:
        return PredictResponse(currencies={}, image="")
        
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image)
        image = Image.open(io.BytesIO(image_data))
        
        # Convert PIL Image to numpy array
        image_np = np.array(image)
        
        # Detect and classify objects
        detected_objects, cropped_images, boxes_and_classes = model.detect_and_collect_objects(image_np)
        classified_objects = model.classify_objects(cropped_images)
        
        # Process results to get currency information
        currencies = {}
        for (class_name, confidence) in classified_objects:
            if class_name not in currencies:
                currencies[class_name] = CurrencyInfo(quantity=1, return_currency_value=0.0)
            else:
                currencies[class_name].quantity += 1
            
            # Here you would calculate the return_currency_value based on the detected currency and the requested return_currency
            # This is just a placeholder, you'll need to implement the actual conversion logic
            currencies[class_name].return_currency_value = model.convert_currency(class_name, request.return_currency)
        
        # Annotate the image
        annotated_image = model.annotate_image(image_np, boxes_and_classes, classified_objects)
        
        # Convert annotated image to base64
        _, buffer = cv2.imencode('.jpg', annotated_image)
        annotated_image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return PredictResponse(currencies=currencies, image=annotated_image_base64)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))