from app.core.config import settings
import tensorflow as tf
class MyModel:
    model = None

    @classmethod
    def load_model(cls, model_path):
        cls.model = tf.keras.models.load_model(settings.MODEL_PATH)

    @classmethod
    def predict(cls, image):
        if cls.model is None:
            cls.load_model(settings.MODEL_PATH)
        results = cls.model(image)
        return results
    
    @classmethod
    def save_processed_image(cls, image_data, filename): #TODO
        # with open(filename, "wb") as f:
        #     f.write(image_data)
        # return filename
        pass
    
model = MyModel()