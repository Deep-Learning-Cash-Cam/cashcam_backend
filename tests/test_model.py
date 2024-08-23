import pytest
from PIL import Image
import numpy as np
from app.ml.model import MyModel
from app.core.config import settings
from PIL import UnidentifiedImageError


#---------------------------------------------- detect_and_collect_objects ----------------------------------------------#


@pytest.mark.parametrize("confidence, expected_count", [
    (0.6, 1),  # Above threshold
    (0.4, 0),  # Below threshold
])
def test_detect_objects_with_varied_confidence(mocker, confidence, expected_count):
    # Mock YOLO model and its response
    YOLO_model = mocker.Mock()
    YOLO_model.names = {0: 'object'}
    boxes_mock = mocker.Mock()
    boxes_mock.xyxy.cpu().numpy.return_value = np.array([[10, 10, 50, 50]])
    boxes_mock.cls.cpu().numpy.return_value = np.array([0])
    boxes_mock.conf.cpu().numpy.return_value = np.array([confidence])

    # Simulate the results object, where [0] returns the mocked boxes
    results_mock = mocker.Mock()
    results_mock.boxes = boxes_mock

    YOLO_model.return_value = [results_mock]  # List-like behavior with a single item

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
    boxes_mock = mocker.Mock()
    boxes_mock.xyxy.cpu().numpy.return_value = detections
    boxes_mock.cls.cpu().numpy.return_value = np.zeros(len(detections))
    boxes_mock.conf.cpu().numpy.return_value = np.ones(len(detections)) * 0.6

    # Simulate the results object, where [0] returns the mocked boxes
    results_mock = mocker.Mock()
    results_mock.boxes = boxes_mock

    YOLO_model.return_value = [results_mock]  # List-like behavior with a single item

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
    boxes_mock = mocker.Mock()
    boxes_mock.xyxy.cpu().numpy.return_value = np.array([[10, 10, 50, 50]])
    boxes_mock.cls.cpu().numpy.return_value = np.array([0])
    boxes_mock.conf.cpu().numpy.return_value = np.array([0.6])

    # Simulate the results object, where [0] returns the mocked boxes
    results_mock = mocker.Mock()
    results_mock.boxes = boxes_mock

    YOLO_model.return_value = [results_mock]  # List-like behavior with a single item

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
    boxes_mock = mocker.Mock()
    boxes_mock.xyxy.cpu().numpy.return_value = np.array([[10, 10, 50, 50]])
    boxes_mock.cls.cpu().numpy.return_value = np.array([0])
    boxes_mock.conf.cpu().numpy.return_value = np.array([0.6])

    # Simulate the results object, where [0] returns the mocked boxes
    results_mock = mocker.Mock()
    results_mock.boxes = boxes_mock

    YOLO_model.return_value = [results_mock]  # List-like behavior with a single item

    # Create a dummy image
    image = Image.new('RGB', (100, 100))

    # Call the method
    cropped_images, boxes_and_classes = MyModel.detect_and_collect_objects(YOLO_model, image, confidence_threshold=0.5)

    # Assertions
    assert len(cropped_images) == 1
    assert boxes_and_classes[0][4] == '1 Euro'  # Verify the detected class name


#--------------------------------------------------- classify_objects ---------------------------------------------------#


@pytest.fixture
def mock_yolo_model(mocker):
    """Fixture to mock the YOLO model and its results."""
    mock_yolo_model = mocker.Mock()

    # Set up mock results to behave like a list
    mock_results = mocker.Mock()
    mock_boxes = mocker.Mock()
    
    # Mock the behavior of the boxes object
    mock_boxes.xyxy.cpu().numpy.return_value = np.array([[0, 0, 10, 10]])
    mock_boxes.cls.cpu().numpy.return_value = np.array([0])
    mock_boxes.conf.cpu().numpy.return_value = np.array([0.9])
    
    # Set mock_results to return boxes when accessed
    mock_results.boxes = mock_boxes
    
    # mock_yolo_model needs to return a list-like object
    mock_yolo_model.return_value = [mock_results]
    
    # Set up names
    mock_yolo_model.names = {0: 'object'}
    
    return mock_yolo_model

@pytest.mark.parametrize(
    "cropped_images, expected_result",
    [
        ([np.zeros((100, 100, 3), dtype=np.uint8)], [('object', 0.9)]),  # Valid case
        ([], []),  # Empty input
        ([np.zeros((10, 10, 3), dtype=np.uint8)], [('object', 0.9)]),  # Small image
    ]
)
def test_classify_objects_with_various_inputs(mock_yolo_model, cropped_images, expected_result):    
    result = MyModel.classify_objects(mock_yolo_model, cropped_images)
    assert result == expected_result

def test_classify_objects_logs_correct_number_when_debug_enabled(mocker, mock_yolo_model):
    settings.DEBUG = True  # Ensure debug mode is enabled
    cropped_images = [np.zeros((100, 100, 3), dtype=np.uint8)]  # Create dummy images

    with mocker.patch('app.logs.logger_config.log') as mock_log:
        MyModel.classify_objects(mock_yolo_model, cropped_images)
        mock_log.assert_called_once_with("Classified 1 objects")

def test_classify_objects_with_invalid_image_handling(mocker, mock_yolo_model):
    mocker.patch("PIL.Image.fromarray", side_effect=UnidentifiedImageError)  # Mock image conversion failure
    cropped_images = [np.zeros((100, 100, 3), dtype=np.uint8)]

    result = MyModel.classify_objects(mock_yolo_model, cropped_images)
    assert result == [('Unknown', 0.0)]  # Expect 'Unknown' for invalid image conversion

@pytest.mark.parametrize(
    "yolo_model_names, expected_result",
    [
        ({0: 'object'}, [('object', 0.9)]),  # Valid YOLO model names
        ({}, [('Unknown', 0.0)]),  # Empty YOLO names
    ]
)
def test_classify_objects_with_various_yolo_names(mocker, mock_yolo_model, yolo_model_names, expected_result):
    mock_yolo_model.names = yolo_model_names
    cropped_images = [np.zeros((100, 100, 3), dtype=np.uint8)]  # Dummy images

    result = MyModel.classify_objects(mock_yolo_model, cropped_images)
    assert result == expected_result

@pytest.mark.parametrize(
    "image_shape, expected_result",
    [
        ((100, 100, 3), [('object', 0.9)]),  # Normal image size
        ((200, 200, 3), [('object', 0.9)]),  # Larger image
        ((50, 50, 3), [('object', 0.9)]),    # Smaller image
    ]
)
def test_classify_objects_with_various_image_sizes(mock_yolo_model, image_shape, expected_result):
    cropped_image = np.zeros(image_shape, dtype=np.uint8)
    cropped_images = [cropped_image]
    
    result = MyModel.classify_objects(mock_yolo_model, cropped_images)
    assert result == expected_result
