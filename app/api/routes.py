from fastapi import APIRouter, HTTPException, UploadFile, File
from app.schemas import PredictRequest, PredictResponse, EncodedImageResponse, EncodedImageRequest
from app.ml.model import MyModel
from fastapi.responses import HTMLResponse, JSONResponse
import requests
from app.services.currency_exchange import exchange_service
import base64
from PIL import Image
import io

model = MyModel()
router = APIRouter()

@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    try:

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
        raise HTTPException(status_code=500, detail=f"Internal error - {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"General error - {str(e)}")
    

@router.post("/encode_image" ,response_model=EncodedImageResponse)
async def upload_image(file: UploadFile = File(...)):
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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/show_image")
async def show_image(request: EncodedImageRequest):
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
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/exchange_rates")
def get_exchange_rates():
    try:
        rates = exchange_service.get_exchange_rates()
        return {"exchange_rates": rates}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))