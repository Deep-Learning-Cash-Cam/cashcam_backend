from app.core.config import settings
class MyModel:
    model = None

    @classmethod
    def load_model(cls, model_path):
        pass

    @classmethod
    def predict(cls, image):
        # if cls.model is None:
        #     raise RuntimeError("Model not loaded. Call load_model first.")
        # results = cls.model(image)
        # return results.pandas().xyxy[0].to_dict(orient="records")
        pass
    
    @classmethod
    def save_processed_image(cls, image_data, filename):
        # with open(filename, "wb") as f:
        #     f.write(image_data)
        # return filename
        pass
    
model = MyModel()