from app.core.config import settings
from ultralytics import YOLO
import cv2
import pandas
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

class MyModel:
    model = None

    @classmethod
    def load_model(cls):
        cls.model = YOLO(settings.MODEL_PATH)

    @classmethod
    def detect_and_collect_objects(cls, image_path, confidence_threshold=0.5):
        detected_objects = {'bill': [], 'coin': []}
        cropped_images = []
        boxes_and_classes = []

        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            print(f"Error loading image: {image_path}")
            return detected_objects, cropped_images, boxes_and_classes

        # Get original image dimensions
        original_height, original_width = img.shape[:2]

        # Convert to RGB (YOLO expects RGB images)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Resize the image to 640x640
        img_resized = cv2.resize(img_rgb, (640, 640))

        # Perform inference on the resized image
        results = cls.model(img_resized)

        # Convert back to original image coordinates
        scale_x = original_width / 640
        scale_y = original_height / 640

        detections = results[0].boxes.xyxy.cpu().numpy()
        classes = results[0].boxes.cls.cpu().numpy()
        confidences = results[0].boxes.conf.cpu().numpy()
        names = cls.model.names

        for i, box in enumerate(detections):
            confidence = confidences[i]
            if confidence < confidence_threshold:
                continue  # Skip detections below the confidence threshold

            # Scale the bounding box coordinates back to the original image size
            x1, y1, x2, y2 = map(int, [box[0] * scale_x, box[1] * scale_y, box[2] * scale_x, box[3] * scale_y])
            class_name = names[int(classes[i])]

            # Crop the detected region
            cropped_img = img_rgb[y1:y2, x1:x2]

            # Add to detected_objects and boxes_and_classes
            detected_objects[class_name].append((cropped_img, confidence))
            boxes_and_classes.append((x1, y1, x2, y2, class_name, confidence))

            # Add to cropped_images
            cropped_images.append(cropped_img)

        return detected_objects, cropped_images, boxes_and_classes

    @classmethod
    def classify_objects(YOLO_model, cropped_images):
        classified_objects = []

        for img in cropped_images:
            original_height, original_width = img.shape[:2]

            # Resize the image to 640x640
            img_resized = cv2.resize(img, (640, 640))

            # Convert to RGB (YOLO expects RGB images)
            img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)

            # Perform inference on the resized image
            results = YOLO_model(img_rgb)

            # Convert back to original image coordinates
            scale_x = original_width / 640
            scale_y = original_height / 640

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
    def annotate_image(image_path, boxes_and_classes, classified_objects):
        img = cv2.imread(image_path)
        if img is None:
            print(f"Error loading image: {image_path}")
            return

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        fig, ax = plt.subplots(1, figsize=(12, 9))
        ax.imshow(img_rgb)

        for (x1, y1, x2, y2, original_class, confidence), (classified_class, class_confidence) in zip(boxes_and_classes, classified_objects):
            rect = Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=2, edgecolor='red', facecolor='none')
            ax.add_patch(rect)

            if classified_class != "Unknown":
                label = f"{classified_class} ({class_confidence:.2f})"
            else:
                label = f"{original_class} ({confidence:.2f}) - Unknown"

            ax.text(x1, y1, label, color='white', fontsize=12, backgroundcolor='red')

        ax.set_title('Original Image with Bounding Boxes and Classifications')
        plt.show()

    @classmethod
    def convert_currency(cls, from_currency, to_currency):
        # Implement currency conversion logic here
        # You might want to use an external API for up-to-date exchange rates
        pass

    @classmethod
    def print_detected_counts(classified_objects):
        counts = {}
        for class_name, _ in classified_objects:
            if class_name in counts:
                counts[class_name] += 1
            else:
                counts[class_name] = 1

        currencies = [
            '0.1 NIS', '0.5 NIS', '1 NIS', '2 NIS', '5 NIS', '10 NIS', '20 NIS', '50 NIS', '100 NIS', '200 NIS',
            '0.01 Euro', '0.02 Euro', '0.05 Euro', '0.1 Euro', '0.2 Euro', '0.5 Euro', '1 Euro', '2 Euro', '5 Euro',
            '10 Euro', '20 Euro', '50 Euro', '100 Euro', '200 Euro', '500 Euro',
            '0.01 USD', '0.05 USD', '0.1 USD', '0.25 USD', '0.5 USD', '1 USD COIN', '1 USD BILL', '2 USD', '5 USD',
            '10 USD', '20 USD', '50 USD', '100 USD'
        ]

        for currency in currencies:
            print(f"{currency}: {counts.get(currency, 0)} images")

model = MyModel()