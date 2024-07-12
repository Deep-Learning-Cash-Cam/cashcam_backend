from pydantic import BaseModel
from typing import List, Dict

class DetectionResponse(BaseModel):
    detections: List[Dict[str, float]]