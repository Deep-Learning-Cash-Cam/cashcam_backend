import pytest
from PIL import Image
import numpy as np
from app.ml.model import MyModel

@pytest.mark.parametrize("confidence, expected_count", [
    (0.6, 1),  # Above threshold
    (0.4, 0),  # Below threshold
])
def test_detect_objects_with_varied_confidence(mocker, confidence, expected_count):
    # Mock YOLO model and its response
    YOLO_model = mocker.Mock()
    YOLO_model.names = {0: 'object'}
    results_mock = mocker.Mock()
    results_mock[0].boxes.xyxy.cpu().numpy.return_value = np.array([[10, 10, 50, 50]])
    results_mock[0].boxes.cls.cpu().numpy.return_value = np.array([0])
    results_mock[0].boxes.conf.cpu().numpy.return_value = np.array([confidence])
    YOLO_model.return_value = results_mock

    # Create a dummy image
    image = Image.new('RGB', (100, 100))

    # Call the method
    cropped_images, boxes_and_classes = MyModel.detect_and_collect_objects(YOLO_model, image, confidence_threshold=0.5)

    # Assertions
    assert len(cropped_images) == expected_count
    assert len(boxes_and_classes) == expected_count

@pytest.mark.parametrize("detections, expected_count", [
    (np.array([[10, 10, 50, 50], [20, 20, 60, 60]]), 2),  # Multiple detections
    (np.array([]), 0),  # No detections
])
def test_handle_multiple_detections(mocker, detections, expected_count):
    # Mock YOLO model and its response
    YOLO_model = mocker.Mock()
    YOLO_model.names = {0: 'object'}
    results_mock = mocker.Mock()
    results_mock[0].boxes.xyxy.cpu().numpy.return_value = detections
    results_mock[0].boxes.cls.cpu().numpy.return_value = np.zeros(len(detections))
    results_mock[0].boxes.conf.cpu().numpy.return_value = np.ones(len(detections)) * 0.6
    YOLO_model.return_value = results_mock

    # Create a dummy image
    image = Image.new('RGB', (100, 100))

    # Call the method
    cropped_images, boxes_and_classes = MyModel.detect_and_collect_objects(YOLO_model, image, confidence_threshold=0.5)

    # Assertions
    assert len(cropped_images) == expected_count
    assert len(boxes_and_classes) == expected_count

def test_invalid_image_input(mocker):
    # Mock YOLO model and its response
    YOLO_model = mocker.Mock()
    YOLO_model.names = {0: 'object'}
    results_mock = mocker.Mock()
    YOLO_model.return_value = results_mock

    # Pass a non-image object
    with pytest.raises(TypeError):
        MyModel.detect_and_collect_objects(YOLO_model, "not_an_image", confidence_threshold=0.5)

def test_correct_cropping(mocker):
    # Mock YOLO model and its response
    YOLO_model = mocker.Mock()
    YOLO_model.names = {0: 'object'}
    results_mock = mocker.Mock()
    results_mock[0].boxes.xyxy.cpu().numpy.return_value = np.array([[10, 10, 50, 50]])
    results_mock[0].boxes.cls.cpu().numpy.return_value = np.array([0])
    results_mock[0].boxes.conf.cpu().numpy.return_value = np.array([0.6])
    YOLO_model.return_value = results_mock

    # Create a dummy image
    image = Image.new('RGB', (100, 100))
    img_array = np.array(image)

    # Call the method
    cropped_images, boxes_and_classes = MyModel.detect_and_collect_objects(YOLO_model, image, confidence_threshold=0.5)

    # Assertions
    assert len(cropped_images) == 1
    assert len(boxes_and_classes) == 1
    # Verify the cropped image matches the expected region
    assert np.array_equal(cropped_images[0], img_array[10:50, 10:50])

def test_currency_detection(mocker):
    # Mock YOLO model and its response for a currency detection
    YOLO_model = mocker.Mock()
    YOLO_model.names = {0: '1 Euro'}
    results_mock = mocker.Mock()
    results_mock[0].boxes.xyxy.cpu().numpy.return_value = np.array([[10, 10, 50, 50]])
    results_mock[0].boxes.cls.cpu().numpy.return_value = np.array([0])
    results_mock[0].boxes.conf.cpu().numpy.return_value = np.array([0.6])
    YOLO_model.return_value = results_mock

    # Create a dummy image
    image = Image.new('RGB', (100, 100))

    # Call the method
    cropped_images, boxes_and_classes = MyModel.detect_and_collect_objects(YOLO_model, image, confidence_threshold=0.5)

    # Assertions
    assert len(cropped_images) == 1
    assert boxes_and_classes[0][4] == '1 Euro'  # Verify the detected class name
