from ultralytics import YOLO

class YOLOModel:
    model = None

    @classmethod
    def load_model(cls, model_path):
        cls.model = YOLO(model_path)

    @classmethod
    def predict(cls, image):
        if cls.model is None:
            raise RuntimeError("Model not loaded. Call load_model first.")
        results = cls.model(image)
        return results.pandas().xyxy[0].to_dict(orient="records")