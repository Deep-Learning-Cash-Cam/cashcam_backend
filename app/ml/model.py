from app.core.config import settings
from ultralytics import YOLO
import numpy as np
from PIL import Image, ImageDraw
from app.schemas.predict_schema import CurrencyInfo
from app.services.currency_exchange import exchange_service
import logging
from app.logs.logger_config import log

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
        results = YOLO_model(image, verbose=False)

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

        log(f"Detected {len(cropped_images)} objects", debug=True)
        return cropped_images, boxes_and_classes

    @classmethod
    def classify_objects(cls, YOLO_model, cropped_images):
        classified_objects = []

        for img in cropped_images:
            # Convert to RGB (YOLO expects RGB images)
            #img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_rgb = Image.fromarray(img).convert("RGB")

            # Perform inference on the original cropped image
            results = YOLO_model(img_rgb, verbose=False)

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

        log(f"Classified {len(classified_objects)} objects", debug=True)
        return classified_objects

    @classmethod
    def annotate_image(cls, image, boxes_and_classes, classified_objects):
        draw = ImageDraw.Draw(image)
        default_color = "red"
        
        for (x1, y1, x2, y2, original_class, confidence), (classified_class, class_confidence) in zip(boxes_and_classes, classified_objects):
            # Draw the bounding box (color based on the classification)
            if classified_class != "Unknown":
                if f"{classified_class}".split(" ")[1] == "NIS":
                    color = "blue"
                elif f"{classified_class}".split(" ")[1] == "Euro":
                    color = "orange"
                elif f"{classified_class}".split(" ")[1] == "USD":
                    color = "green"
            else:
                color = default_color
                
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            
            # Create the label
            if classified_class != "Unknown":
                label = f"{classified_class} ({class_confidence:.2f})"
            else:
                label = f"{original_class} ({confidence:.2f}) - Unknown"
        
            # Draw the label
            text_bbox = draw.textbbox((x1, y1), label)
            draw.rectangle(text_bbox, fill= color)
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

        # Create a dictionary with the detected counts for each currency and remove any currencies with 0 counts
        # Also, split the class name to the currency and the value ('0.1 NIS' -> 'NIS', (0.1, count))
        detected_currencies = {}
        for class_name, count in counts.items():
            if class_name != "Unknown":
                multiplier = class_name.split(" ")[0]
                if class_name in cls.currencies_dict:
                    # Transform the detected currencies to the 'currency' structure
                    detected_currencies[cls.currencies_dict[class_name]] = CurrencyInfo(quantity= count, return_currency_value= float(multiplier))
                else:
                    log(f"Warning: Unknown currency class name '{class_name}'", logging.CRITICAL)
                    continue
                
        currencies = MyModel.calculate_return_currency_value(detected_currencies, return_currency)
        
        log(f"Detected currencies with exchange rates added: {currencies}", debug=True)
        return currencies
    
    @classmethod
    def calculate_return_currency_value(cls, detected_currencies, return_currency):
        try:
            exchange_rates = exchange_service.get_exchange_rates()
            
            log(f"Exchange rates: {exchange_rates}", debug=True)
            log(f"Before calculating exchange rate values: {detected_currencies} - {return_currency}", debug=True)
            
            # ------- Inner function ------- #
            def get_exchange_rate_inner_func(from_currency, to_currency):
                if from_currency == to_currency:
                    return 1.0
                key = f"{from_currency}_{to_currency}"
                if key in exchange_rates:
                    return exchange_rates[key]
                inverse_key = f"{to_currency}_{from_currency}"
                if inverse_key in exchange_rates:
                    return 1 / exchange_rates[inverse_key]
                return None
            # ------- Inner function ------- #

            updated_currencies = {}
            for coin_label, data in detected_currencies.items():
                coin_name = coin_label.split("_")[0]
                if coin_name == "NIS": # Replace NIS with ILS
                    coin_name = "ILS"
                elif coin_name == "Unknown": # Skip unknown currencies
                    updated_currencies[coin_name] = CurrencyInfo(quantity= data.quantity, return_currency_value= 0.0)
                    continue
                
                rate = get_exchange_rate_inner_func(coin_name, return_currency)
                if rate is not None:
                    if coin_name == "ILS": # Replace ILS with NIS
                        coin_name = "NIS"
                    return_value = round(rate * data.return_currency_value, 2)
                    updated_currencies[coin_label] = CurrencyInfo(quantity= data.quantity, return_currency_value= return_value)
                else:
                    log(f"Warning: No exchange rate found for {coin_name} to {return_currency}", logging.CRITICAL)
                    updated_currencies[coin_label] = CurrencyInfo(quantity= data.quantity, return_currency_value= 0.0)

            log(f"Calculated exchange rates", debug=True)
            return updated_currencies
        
        except Exception as e:
            log(f"Error in calculating the return currency value - {str(e)}", logging.CRITICAL)
            raise ValueError("Error in calculating the return currency value")
    
    @classmethod
    def predict_image(cls, image: Image, return_currency: str, confidence_threshold=0.5):
        try:
            cropped_images, boxes_and_classes = cls.detect_and_collect_objects(cls.object_detection_model, image, confidence_threshold= confidence_threshold)
            classified_objects = cls.classify_objects(cls.classification_model, cropped_images)
            annotated_image = cls.annotate_image(image, boxes_and_classes, classified_objects)
            currencies = cls.get_detected_counts(classified_objects, return_currency)
        except Exception as e:
            log(f"Error in predicting the image - {str(e)}", logging.CRITICAL)
            raise ValueError("Error in predicting the image")
        return annotated_image, currencies

model = MyModel()