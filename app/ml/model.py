from app.core.config import settings
from ultralytics import YOLO
import numpy as np
from PIL import Image, ImageDraw
from app.schemas.response import CurrencyInfo

class MyModel:
    object_detection_model = YOLO(settings.OBJECT_DETECTION_MODEL)
    classification_model = YOLO(settings.CLASSIFICATION_MODEL)
    currencies_dict = { # Dictionary mapping the class names to the currency names (keys related to the model and values relate to the app's label)
        '0.1 NIS':'NIS_C_10', '0.5 NIS':'NIS_C_50', '1 NIS':'NIS_C_100', '2 NIS':'NIS_C_200', '5 NIS':'NIS_C_500', '10 NIS':'NIS_C_1000',
        '20 NIS':'NIS_B_20', '50 NIS':'NIS_B_50', '100 NIS':'NIS_B_100', '200 NIS':'NIS_B_200',
        '0.01 Euro':'EUR_C_1', '0.02 Euro':'EUR_C_2', '0.05 Euro':'EUR_C_5', '0.1 Euro':'EUR_C_10', '0.2 Euro':'EUR_C_20', '0.5 Euro':'EUR_C_50', '1 Euro':'EUR_C_100', '2 Euro':'EUR_C_200',
        '5 Euro':'EUR_B_5', '10 Euro':'EUR_B_10', '20 Euro':'EUR_B_20', '50 Euro':'EUR_B_50', '100 Euro':'EUR_B_100', '200 Euro':'EUR_B_200', '500 Euro':'EUR_B_500',
        '0.01 USD':'USD_C_1', '0.05 USD':'USD_C_5', '0.1 USD':'USD_C_10', '0.25 USD':'USD_C_25', '0.5 USD':'USD_C_50', '1 USD COIN':'USD_C_100',
        '1 USD BILL':'USD_B_1', '2 USD':'USD_B_2', '5 USD':'USD_B_5', '10 USD':'USD_B_10', '20 USD':'USD_B_20', '50 USD':'USD_B_50', '100 USD':'USD_B_100',
        'Unknown':'Unknown'
        }

    @classmethod
    def detect_and_collect_objects(cls, YOLO_model, image, confidence_threshold=0.5):
        cropped_images = []
        boxes_and_classes = []

        # Convert from PIL to numpy array
        img_np = np.array(image)

        # Detect objects in the image
        results = YOLO_model(image)

        detections = results[0].boxes.xyxy.cpu().numpy()
        classes = results[0].boxes.cls.cpu().numpy()
        confidences = results[0].boxes.conf.cpu().numpy()
        names = YOLO_model.names
        
        for i, box in enumerate(detections):
            confidence = confidences[i]
            if confidence < confidence_threshold:
                continue  # Skip detections below the confidence threshold

            x1, y1, x2, y2 = map(int, box)
            class_name = names[int(classes[i])]

            # Crop the detected region
            cropped_img = img_np[y1:y2, x1:x2]

            # Add to detected_objects and boxes_and_classes
            boxes_and_classes.append((x1, y1, x2, y2, class_name, confidence))

            # Add to cropped_images
            cropped_images.append(cropped_img)

        return cropped_images, boxes_and_classes

    @classmethod
    def classify_objects(cls, YOLO_model, cropped_images):
        classified_objects = []

        for img in cropped_images:
            # Convert to RGB (YOLO expects RGB images)
            #img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_rgb = Image.fromarray(img).convert("RGB")

            # Perform inference on the original cropped image
            results = YOLO_model(img_rgb)

            detections = results[0].boxes.xyxy.cpu().numpy()
            classes = results[0].boxes.cls.cpu().numpy()
            confidences = results[0].boxes.conf.cpu().numpy()
            names = YOLO_model.names

            if len(detections) > 0:
                class_name = names[int(classes[0])]
                confidence = confidences[0]
                classified_objects.append((class_name, confidence))
            else:
                classified_objects.append(("Unknown", 0.0))

        return classified_objects

    @classmethod
    def annotate_image(cls, image, boxes_and_classes, classified_objects):
        draw = ImageDraw.Draw(image)
        
        for (x1, y1, x2, y2, original_class, confidence), (classified_class, class_confidence) in zip(boxes_and_classes, classified_objects):
            # Draw the bounding box
            draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
        
            # Create the label
            if classified_class != "Unknown":
                label = f"{classified_class} ({class_confidence:.2f})"
            else:
                label = f"{original_class} ({confidence:.2f}) - Unknown"
        
            # Draw the label
            text_bbox = draw.textbbox((x1, y1), label)
            draw.rectangle(text_bbox, fill="red")
            draw.text((x1, y1), label, fill="white")
            
        #Convert the image to PIL format
        image = Image.fromarray(np.array(image))
        
        return image

    @classmethod
    def get_detected_counts(cls, classified_objects, return_currency):
        counts = {}
        for class_name, _ in classified_objects:
            if class_name in counts:
                counts[class_name] += 1
            else:
                counts[class_name] = 1

        try:
            # Create a dictionary with the detected counts for each currency and remove any currencies with 0 counts
            # Also swap the class names with the currency names using the currencies_dict
            detected_currencies = {MyModel.currencies_dict.get(class_name): count for class_name, count in counts.items()}
            detected_currencies = {k: v for k, v in detected_currencies.items() if v > 0}
        except:
            raise ValueError("Currency not found in currencies_dict")
        
        currencies = MyModel.calculate_return_currency_value(detected_currencies, return_currency)
        return currencies
    
    @classmethod
    def calculate_return_currency_value(cls, detected_currencies, return_currency):
        currencies = {}
        
        #TODO: Add the conversion rates here using API
        
        # Transform the detected currencies to the 'currency' structure
        for currency, count in detected_currencies.items():
            currencies[currency] = CurrencyInfo(quantity=count, return_currency_value=1.0) # Placeholder

        print(f"Detected currencies: {currencies}")
        return currencies

model = MyModel()