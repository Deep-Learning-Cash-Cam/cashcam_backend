from fastapi import APIRouter, HTTPException, UploadFile, File
from app.schemas import PredictRequest, PredictResponse, CurrencyInfo, EncodedImage
from app.ml.model import MyModel
from fastapi.responses import HTMLResponse, JSONResponse
import base64
from PIL import Image
import io
import numpy as np
from ultralytics import YOLO
import cv2

router = APIRouter()
model = MyModel()
object_detection_model = model.object_detection_model
classification_model = model.classification_model

@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image)
        image = Image.open(io.BytesIO(image_data))
        
        # Detect and classify objects
        detected_objects, cropped_images, boxes_and_classes = model.detect_and_collect_objects(object_detection_model, image, confidence_threshold=0.5)
        classified_objects = model.classify_objects(classification_model, cropped_images)
        model.annotate_image(image, boxes_and_classes, classified_objects)
        detected_currencies = model.get_detected_counts(classified_objects)
        
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
    

@router.post("/encode_image" ,response_model=EncodedImage)
async def upload_image(file: UploadFile = File(...)):
    try:
        
        # Read the image
        image = Image.open(io.BytesIO(await file.read()))
        
        image = image.convert("RGB")
        Buffered = io.BytesIO()
        image.save(Buffered, format="JPEG")
        img_str = base64.b64encode(Buffered.getvalue()).decode()
        return JSONResponse(content={"image": img_str}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/show_image",response_model=EncodedImage)
async def show_image(request: EncodedImage):
    try:
        try:
            image_data = base64.b64decode(request.image)
            image = Image.open(io.BytesIO(image_data))
            image = image.convert("RGB")
        except:
            raise HTTPException(status_code=400, detail="Invalid image data")
        
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
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
        raise HTTPException(status_code=500, detail=str(e))

