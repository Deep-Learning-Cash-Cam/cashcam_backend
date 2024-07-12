from fastapi import APIRouter, File, UploadFile, Query
from app.ml.model import YOLOModel
from app.schemas.response import DetectionResponse

router = APIRouter()

@router.post("/detect", response_model=DetectionResponse)
async def detect_objects(file: UploadFile = File(...)):
    contents = await file.read()
    results = YOLOModel.predict(contents)
    return DetectionResponse(detections=results)