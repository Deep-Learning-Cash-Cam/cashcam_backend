import pytest
import logging
import numpy as np
from PIL import Image, ImageDraw
from app.ml.model import MyModel
from app.core.config import settings
from PIL import UnidentifiedImageError
from app.schemas.predict_schema import CurrencyInfo
from app.services.currency_exchange import exchange_service


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
    
    mock_log = mocker.patch('app.ml.model.log')  # Adjust the path to the correct logging function
    
    MyModel.classify_objects(mock_yolo_model, cropped_images)
    
    mock_log.assert_called_once_with("Classified 1 objects") # Classified 1 image as 'unknown'

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


#---------------------------------------------------- annotate_image ----------------------------------------------------#


@pytest.fixture
def blank_image():
    return Image.new('RGB', (100, 100), color='white')

@pytest.fixture
def high_res_image():
    return Image.new('RGB', (1920, 1080), color='white')

class TestAnnotateImage:

    # Account for slight variations in color due to anti-aliasing or image processing
    def assert_color_close(actual_color, expected_color, tolerance=15):
        return all(abs(a - e) <= tolerance for a, e in zip(actual_color, expected_color))

    # Check for color assignment and correct drawing for known classes
    def test_annotate_image_known_classes(self, blank_image):
        boxes_and_classes = [(10, 10, 50, 50, 'Currency', 0.9)]
        classified_objects = [('USD Dollar', 0.95)]

        annotated_image = MyModel.annotate_image(blank_image, boxes_and_classes, classified_objects)
        annotated_array = np.array(annotated_image)

        # Ensure image has been drawn on
        assert not np.all(annotated_array == 255)

        # Print the actual color at the pixel for debugging
        print("Pixel color at (10, 10):", annotated_array[10, 10])

        for y in range(10, 20):
            for x in range(10, 20):
                print(f"Pixel color at ({x}, {y}):", annotated_array[y, x])

        # Check color for USD (allowing some tolerance)
        assert TestAnnotateImage.assert_color_close(annotated_array[10, 10], [0, 128, 0])  # Green for USD

    # Check for correct handling of "Unknown" classes
    def test_annotate_image_unknown_class(self, blank_image):
        boxes_and_classes = [(10, 10, 50, 50, 'Currency', 0.9)]
        classified_objects = [('Unknown', 0.0)]

        annotated_image = MyModel.annotate_image(blank_image, boxes_and_classes, classified_objects)
        annotated_array = np.array(annotated_image)

        assert not np.all(annotated_array == 255)

        # Check that the color is red for "Unknown"
        assert (annotated_array[10, 10] == [255, 0, 0]).all()

    # Check for currency-specific color assignments
    def test_annotate_image_currency_colors(self, blank_image):
        boxes_and_classes = [(10, 10, 50, 50, 'Currency', 0.9)]
        classified_objects = [('Euro', 0.95)]

        annotated_image = MyModel.annotate_image(blank_image, boxes_and_classes, classified_objects)
        annotated_array = np.array(annotated_image)

        assert not np.all(annotated_array == 255)

        # Print the actual color at the pixel for debugging
        print("Pixel color at (10, 10):", annotated_array[15, 15])

        # Check that the color is orange for Euro
        assert (annotated_array[10, 10] == [255, 165, 0]).all()

    # Ensure correct handling of multiple objects in an image
    def test_annotate_image_multiple_objects(self, blank_image): 
        boxes_and_classes = [
            (10, 10, 30, 30, 'Currency', 0.9),  # Smaller USD box
            (40, 40, 60, 60, 'Currency', 0.8)   # Separate Euro box
        ]
        classified_objects = [('USD Dollar', 0.95), ('Euro', 0.85)]

        annotated_image = MyModel.annotate_image(blank_image, boxes_and_classes, classified_objects)
        annotated_array = np.array(annotated_image)

        assert not np.all(annotated_array == 255)

        # Debugging prints
        print("Pixel color at (15, 15):", annotated_array[15, 15])  # Inside USD box
        print("Pixel color at (45, 45):", annotated_array[45, 45])  # Inside Euro box

        # Check color for USD (allowing some tolerance)
        assert TestAnnotateImage.assert_color_close(annotated_array[20, 20], [0, 128, 0], tolerance=15)  # Green for USD

        # Check color for Euro (allowing some tolerance)
        assert TestAnnotateImage.assert_color_close(annotated_array[45, 45], [255, 165, 0], tolerance=15)  # Orange for Euro

    # Test for cases where the classified_class does not have a space
    def test_annotate_image_classified_class_no_space(self, blank_image):
        boxes_and_classes = [(10, 10, 50, 50, 'Currency', 0.9)]
        classified_objects = [('USDDollar', 0.95)]

        annotated_image = MyModel.annotate_image(blank_image, boxes_and_classes, classified_objects)
        annotated_array = np.array(annotated_image)

        assert not np.all(annotated_array == 255)

    # Test performance on high-resolution images
    def test_annotate_image_high_resolution(self, high_res_image):
        boxes_and_classes = [(100, 100, 500, 500, 'Currency', 0.9)]
        classified_objects = [('USD Dollar', 0.95)]

        annotated_image = MyModel.annotate_image(high_res_image, boxes_and_classes, classified_objects)
        annotated_array = np.array(annotated_image)

        assert not np.all(annotated_array == 255)

    # Ensure method handles images without classified objects gracefully
    def test_annotate_image_no_classified_objects(self, blank_image):
        boxes_and_classes = []
        classified_objects = []

        annotated_image = MyModel.annotate_image(blank_image, boxes_and_classes, classified_objects)
        annotated_array = np.array(annotated_image)

        assert np.all(annotated_array == 255)  # Image should remain blank

    # Verifies that labels are formatted correctly
    def test_annotate_image_label_formatting(self, blank_image):
        boxes_and_classes = [(10, 10, 50, 50, 'Currency', 0.9)]
        classified_objects = [('USD Dollar', 0.95)]

        annotated_image = MyModel.annotate_image(blank_image, boxes_and_classes, classified_objects)
        annotated_array = np.array(annotated_image)

        assert not np.all(annotated_array == 255)

        # Mocking actual text drawing can be done if needed


#-------------------------------------------------- get_detected_counts --------------------------------------------------#


class TestGetDetectedCounts:

    # Test that currencies are correctly counted from classified objects
    def test_correct_currency_count(self, mocker):
        classified_objects = [('0.1 NIS', 1), ('0.1 NIS', 1), ('1 USD BILL', 1)]
        return_currency = 'USD'
    
        mocker.patch.object(MyModel, 'currencies_dict', {
            '0.1 NIS': 'NIS_C_10', 
            '1 USD BILL': 'USD_B_1'
        })
        mocker.patch.object(MyModel, 'calculate_return_currency_value', return_value={
            'NIS_C_10': CurrencyInfo(quantity=2, return_currency_value=0.1),
            'USD_B_1': CurrencyInfo(quantity=1, return_currency_value=1.0)
        })
    
        result = MyModel.get_detected_counts(classified_objects, return_currency)
    
        assert result['NIS_C_10'].quantity == 2
        assert result['NIS_C_10'].return_currency_value == 0.1
        assert result['USD_B_1'].quantity == 1
        assert result['USD_B_1'].return_currency_value == 1.0

    # Test handling unknown currency classes with logging
    def test_handles_unknown_currency_classes(self, mocker):
        classified_objects = [('Unknown', 1), ('0.5 NIS', 1)]
        return_currency = 'USD'
    
        mocker.patch.object(MyModel, 'currencies_dict', {
            '0.5 NIS': 'NIS_C_50'
        })
        mocker.patch.object(MyModel, 'calculate_return_currency_value', return_value={
            'NIS_C_50': CurrencyInfo(quantity=1, return_currency_value=0.5)
        })
    
        log_mock = mocker.patch('app.ml.model.log')
    
        result = MyModel.get_detected_counts(classified_objects, return_currency)
    
        log_mock.assert_any_call("Warning: Unknown currency class name 'Unknown'", logging.CRITICAL)
        assert 'NIS_C_50' in result
        assert result['NIS_C_50'].quantity == 1
        assert result['NIS_C_50'].return_currency_value == 0.5

    # Test that detected currencies are properly mapped to their labels
    def test_properly_maps_detected_currencies(self, mocker):
        classified_objects = [('0.1 NIS', 1), ('0.1 NIS', 1), ('1 USD BILL', 1)]
        return_currency = 'USD'

        mocker.patch.object(MyModel, 'currencies_dict', {
            '0.1 NIS': 'NIS_C_10',
            '1 USD BILL': 'USD_B_1'
        })
        mocker.patch.object(MyModel, 'calculate_return_currency_value', return_value={
            'NIS_C_10': CurrencyInfo(quantity=2, return_currency_value=0.1),
            'USD_B_1': CurrencyInfo(quantity=1, return_currency_value=1.0)
        })
    
        result = MyModel.get_detected_counts(classified_objects, return_currency)

        assert result['NIS_C_10'].quantity == 2
        assert result['NIS_C_10'].return_currency_value == 0.1
        assert result['USD_B_1'].quantity == 1
        assert result['USD_B_1'].return_currency_value == 1.0

    # Test logging of detected currencies with exchange rates in debug mode
    def test_log_detected_currencies_in_debug_mode(self, mocker):
        classified_objects = [('0.1 NIS', 1), ('0.1 NIS', 1), ('1 USD BILL', 1)]
        return_currency = 'USD'
        mocker.patch.object(MyModel, 'currencies_dict', {
            '0.1 NIS': 'NIS_C_10',
            '1 USD BILL': 'USD_B_1'
        })
        mocker.patch.object(MyModel, 'calculate_return_currency_value', return_value={
            'NIS_C_10': CurrencyInfo(quantity=2, return_currency_value=0.1),
            'USD_B_1': CurrencyInfo(quantity=1, return_currency_value=1.0)
        })
        mock_log = mocker.patch('app.ml.model.log')
        mocker.patch('app.ml.model.settings.DEBUG', True)

        result = MyModel.get_detected_counts(classified_objects, return_currency)

        assert result['NIS_C_10'].quantity == 2
        assert result['USD_B_1'].quantity == 1
        mock_log.assert_called_with("Detected currencies with exchange rates added: "
                                    "{'NIS_C_10': CurrencyInfo(quantity=2, return_currency_value=0.1), 'USD_B_1': CurrencyInfo(quantity=1, return_currency_value=1.0)}")

    # Test handling of an empty classified objects list
    def test_empty_classified_objects_list(self, mocker):
        classified_objects = []
        return_currency = 'USD'

        mocker.patch.object(MyModel, 'currencies_dict', {})
        mocker.patch.object(MyModel, 'calculate_return_currency_value', return_value={})

        result = MyModel.get_detected_counts(classified_objects, return_currency)

        assert result == {}

    # Test logging a warning for unknown currency class names
    def test_logs_warning_for_unknown_currency(self, mocker):
        classified_objects = [('0.1 NIS', 1), ('Unknown', 1)]
        return_currency = 'USD'

        mocker.patch.object(MyModel, 'currencies_dict', {
            '0.1 NIS': 'NIS_C_10'
        })
        log_mock = mocker.patch('app.ml.model.log')

        result = MyModel.get_detected_counts(classified_objects, return_currency)

        # Use assert_any_call to verify the warning message was logged
        log_mock.assert_any_call("Warning: Unknown currency class name 'Unknown'", logging.CRITICAL)
        assert 'NIS_C_10' in result

    # Test handling cases where no objects are detected
    def test_no_objects_detected(self, mocker):
        classified_objects = []
        return_currency = 'USD'

        mocker.patch.object(MyModel, 'currencies_dict', {})
        mocker.patch.object(MyModel, 'calculate_return_currency_value', return_value={})

        result = MyModel.get_detected_counts(classified_objects, return_currency)

        assert result == {}

    # Test that unknown currency class counts are not included in the result
    def test_no_unknown_counts_in_result(self, mocker):
        classified_objects = [('0.1 NIS', 1), ('Unknown', 1)]
        return_currency = 'USD'

        mocker.patch.object(MyModel, 'currencies_dict', {
            '0.1 NIS': 'NIS_C_10',
            'Unknown': 'Unknown'
        })
        mocker.patch.object(MyModel, 'calculate_return_currency_value', return_value={
            'NIS_C_10': CurrencyInfo(quantity=1, return_currency_value=0.1)
        })

        result = MyModel.get_detected_counts(classified_objects, return_currency)

        assert 'Unknown' not in result
        assert 'NIS_C_10' in result

    # Test that return currency values are calculated even when exchange rates are missing
    def test_handles_missing_exchange_rates(self, mocker):
        classified_objects = [('0.1 NIS', 1), ('1 USD BILL', 1)]
        return_currency = 'USD'

        mocker.patch.object(MyModel, 'currencies_dict', {
            '0.1 NIS': 'NIS_C_10',
            '1 USD BILL': 'USD_B_1'
        })
        
        # Mock calculate_return_currency_value to handle missing exchange rates
        mocker.patch.object(MyModel, 'calculate_return_currency_value', return_value={
            'NIS_C_10': CurrencyInfo(quantity=1, return_currency_value=0.0),  # Missing exchange rate for NIS
            'USD_B_1': CurrencyInfo(quantity=1, return_currency_value=1.0)   # Exchange rate for USD
        })

        result = MyModel.get_detected_counts(classified_objects, return_currency)

        assert 'NIS_C_10' in result
        assert 'USD_B_1' in result
        assert result['NIS_C_10'].return_currency_value == 0.0  # No exchange rate, value should be 0.0
        assert result['USD_B_1'].return_currency_value == 1.0  # USD should have its value correctly calculated


#-------------------------------------------- calculate_return_currency_value --------------------------------------------#


class TestCalculateReturnCurrencyValue:

    # Test correctly calculating return values for known currencies
    def test_known_currencies(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value={
            'USD_ILS': 3.5,
            'EUR_ILS': 4.0
        })
        mocker.patch.object(settings, 'DEBUG', False)

        detected_currencies = {
            'USD_1': CurrencyInfo(quantity=1, return_currency_value=100.0),
            'EUR_1': CurrencyInfo(quantity=1, return_currency_value=200.0)
        }

        expected_result = {
            'USD_1': CurrencyInfo(quantity=1, return_currency_value=350.0),
            'EUR_1': CurrencyInfo(quantity=1, return_currency_value=800.0)
        }

        result = MyModel.calculate_return_currency_value(detected_currencies, 'ILS')
        assert result == expected_result

    # Test handling of unknown currencies
    def test_unknown_currencies(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value={
            'USD_ILS': 3.5
        })
        mocker.patch.object(settings, 'DEBUG', False)

        detected_currencies = {
            'Unknown_1': CurrencyInfo(quantity=1, return_currency_value=100.0)
        }

        expected_result = {
            'Unknown': CurrencyInfo(quantity=1, return_currency_value=0.0)
        }

        result = MyModel.calculate_return_currency_value(detected_currencies, 'ILS')
        assert result == expected_result

    # Test handling of identical currencies (USD to USD)
    def test_identical_currency(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value={
            'USD_ILS': 3.5,
            'EUR_ILS': 4.0
        })
        mocker.patch.object(settings, 'DEBUG', False)

        detected_currencies = {
            'USD_1': CurrencyInfo(quantity=1, return_currency_value=100.0)
        }

        result = MyModel.calculate_return_currency_value(detected_currencies, 'USD')
        assert result['USD_1'].return_currency_value == 100.0

    # Test logging when DEBUG is True
    def test_logs_when_debug_true(self, mocker, caplog):
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value={
            'USD_ILS': 3.5,
            'EUR_ILS': 4.0
        })
        mocker.patch.object(settings, 'DEBUG', True)

        detected_currencies = {
            'USD_1': CurrencyInfo(quantity=1, return_currency_value=100.0),
            'EUR_1': CurrencyInfo(quantity=1, return_currency_value=200.0)
        }

        with caplog.at_level(logging.INFO):
            MyModel.calculate_return_currency_value(detected_currencies, 'ILS')
            assert "Exchange rates" in caplog.text
            assert "Before calculating exchange rate values" in caplog.text
            assert "Calculated exchange rates" in caplog.text

    # Test for missing exchange rates handling with log warning
    def test_logs_warning_no_exchange_rate(self, mocker, caplog):
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value={})
        mocker.patch.object(settings, 'DEBUG', False)

        detected_currencies = {
            'USD_1': CurrencyInfo(quantity=1, return_currency_value=100.0)
        }

        with caplog.at_level(logging.CRITICAL):
            result = MyModel.calculate_return_currency_value(detected_currencies, 'ILS')
            assert result['USD_1'].return_currency_value == 0.0
            assert "Warning: No exchange rate found for USD to ILS" in caplog.text

    # Test handling of empty detected_currencies input
    def test_empty_detected_currencies(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value={})
        mocker.patch.object(settings, 'DEBUG', False)

        result = MyModel.calculate_return_currency_value({}, 'ILS')
        assert result == {}

    # Test inverse exchange rates
    def test_inverse_exchange_rate(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value={
            'ILS_USD': 0.28
        })
        mocker.patch.object(settings, 'DEBUG', False)

        detected_currencies = {
            'ILS_1': CurrencyInfo(quantity=1, return_currency_value=100.0)
        }

        expected_result = {
            'ILS_1': CurrencyInfo(quantity=1, return_currency_value=28.0)
        }

        result = MyModel.calculate_return_currency_value(detected_currencies, 'USD')
        assert result == expected_result

    # Test exception handling and logging errors
    def test_exception_handling(self, mocker, caplog):
        mocker.patch.object(exchange_service, 'get_exchange_rates', side_effect=Exception("Mocked exception"))
        mocker.patch.object(settings, 'DEBUG', False)

        detected_currencies = {
            'USD_1': CurrencyInfo(quantity=1, return_currency_value=100.0)
        }

        with caplog.at_level(logging.CRITICAL):
            with pytest.raises(Exception):
                MyModel.calculate_return_currency_value(detected_currencies, 'ILS')
            assert "Error in calculating the return currency value" in caplog.text

    # Test special cases handling for "NIS" to "ILS" conversions
    def test_special_cases_nis_ils(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value={
            'USD_ILS': 3.5,
            'ILS_EUR': 0.25,
            'USD_EUR': 0.286
        })
        mocker.patch.object(settings, 'DEBUG', False)

        detected_currencies = {
            'USD_1': CurrencyInfo(quantity=1, return_currency_value=100.0),
            'NIS_1': CurrencyInfo(quantity=1, return_currency_value=50.0)
        }

        expected_result = {
            'USD_1': CurrencyInfo(quantity=1, return_currency_value=28.6),  # USD to EUR (100 * 0.286)
            'NIS_1': CurrencyInfo(quantity=1, return_currency_value=12.5)   # NIS to EUR (50 * 0.25)
        }

        result = MyModel.calculate_return_currency_value(detected_currencies, 'EUR')
        assert result == expected_result



#-------------------------------------------------------- MyModel --------------------------------------------------------#


class TestMyModel:
    def test_detect_objects_high_confidence(self, mocker):
        # Mock the YOLO model and its results
        mock_yolo_model = mocker.Mock()
        mock_boxes = mocker.Mock()
        mock_boxes.xyxy.cpu().numpy.return_value = np.array([[10, 10, 50, 50]])
        mock_boxes.cls.cpu().numpy.return_value = np.array([0])
        mock_boxes.conf.cpu().numpy.return_value = np.array([0.9])
        
        # Set up mock_results as a list-like object with index 0 returning mock_boxes
        mock_first_result = mocker.Mock()
        mock_first_result.boxes = mock_boxes
        
        # Simulate that mock_yolo_model returns a list with one item
        mock_yolo_model.return_value = [mock_first_result]
        mock_yolo_model.names = {0: '0.1 NIS'}

        # Create a dummy image
        image = Image.new('RGB', (100, 100))

        # Call the method under test
        cropped_images, boxes_and_classes = MyModel.detect_and_collect_objects(mock_yolo_model, image, confidence_threshold=0.5)

        # Assertions
        assert len(cropped_images) == 1
        assert len(boxes_and_classes) == 1
        assert boxes_and_classes[0][4] == '0.1 NIS'
        assert 10 <= boxes_and_classes[0][0] < 50  # Check bounding box coordinates

    def test_classify_cropped_images_correctly(self, mocker):
        # Mock the YOLO model and its results
        mock_yolo_model = mocker.Mock()
        mock_boxes = mocker.Mock()
        mock_boxes.xyxy.cpu().numpy.return_value = np.array([[10, 10, 50, 50]])
        mock_boxes.cls.cpu().numpy.return_value = np.array([0])
        mock_boxes.conf.cpu().numpy.return_value = np.array([0.9])
        
        # Set up mock_results as a list-like object with index 0 returning mock_boxes
        mock_first_result = mocker.Mock()
        mock_first_result.boxes = mock_boxes
        
        # Simulate that mock_yolo_model returns a list with one item
        mock_yolo_model.return_value = [mock_first_result]
        mock_yolo_model.names = {0: '0.1 NIS'}

        # Create a dummy image
        image = Image.new('RGB', (100, 100))

        # Call the method under test
        cropped_images, boxes_and_classes = MyModel.detect_and_collect_objects(mock_yolo_model, image, confidence_threshold=0.5)
        classified_objects = MyModel.classify_objects(mock_yolo_model, cropped_images)

        # Assertions
        assert len(cropped_images) == 1
        assert len(classified_objects) == 1
        assert classified_objects[0][0] == '0.1 NIS'
        assert classified_objects[0][1] == 0.9

    def test_annotate_image_with_bounding_boxes(self, mocker):
        # Mock the input data
        image = Image.new('RGB', (100, 100))
        boxes_and_classes = [(10, 10, 50, 50, '0.1 NIS', 0.9)]
        classified_objects = [('NIS_C_10', 0.9)]

        # Mock the ImageDraw module
        mock_draw = mocker.Mock()
        mocker.patch('app.ml.model.ImageDraw.Draw', return_value=mock_draw)

        # Mock the textbbox method
        expected_text_bbox = [10, 10, 60, 30]  # Example coordinates; adjust as needed
        mock_draw.textbbox = mocker.Mock(return_value=expected_text_bbox)

        # Call the method under test
        annotated_image = MyModel.annotate_image(image, boxes_and_classes, classified_objects)

        # Assertions
        assert annotated_image is not None

        # Ensure two rectangles were drawn: one for the bounding box, one for the label background
        assert mock_draw.rectangle.call_count == 2

        # Check the bounding box rectangle call
        bounding_box_call = mock_draw.rectangle.call_args_list[0]
        assert bounding_box_call == mocker.call([10, 10, 50, 50], outline='blue', width=2)

        # Check the label background rectangle call
        text_box_call = mock_draw.rectangle.call_args_list[1]
        assert text_box_call == mocker.call(expected_text_bbox, fill='blue')

        # Ensure the text was drawn once
        assert mock_draw.text.call_count == 1

        # Check the text drawing arguments
        mock_draw.text.assert_called_with((10, 10), 'NIS_C_10 (0.90)', fill='white')

    def test_log_messages_debug_enabled(self, mocker):
        # Mock settings.DEBUG to True
        mocker.patch('app.core.config.settings.DEBUG', True)

        # Mock the log function
        mock_log = mocker.patch('app.ml.model.log')

        # Mock YOLO model and its response with zero detections
        YOLO_model = mocker.Mock()
        YOLO_model.names = {}
        boxes_mock = mocker.Mock()
        boxes_mock.xyxy.cpu().numpy.return_value = np.array([])  # No detections
        boxes_mock.cls.cpu().numpy.return_value = np.array([])
        boxes_mock.conf.cpu().numpy.return_value = np.array([])

        # Simulate the results object with zero detections
        results_mock = mocker.Mock()
        results_mock.boxes = boxes_mock
        YOLO_model.return_value = [results_mock]  # List-like behavior with a single item

        # Create a dummy image
        image = Image.new('RGB', (100, 100))

        # Call the method under test
        cropped_images, boxes_and_classes = MyModel.detect_and_collect_objects(YOLO_model, image)

        # Assertions
        mock_log.assert_called_once_with("Detected 0 objects")

    def test_calculate_return_currency_value(self, mocker):
        # Mock the exchange service
        mock_exchange_service = mocker.MagicMock()
        mock_exchange_service.get_exchange_rates.return_value = {
            'EUR_USD': 1.1162,
            'EUR_ILS': 4.1228,
            'USD_EUR': 0.8959,
            'USD_ILS': 3.6947,
            'ILS_EUR': 0.2426,
            'ILS_USD': 0.2705
        }

        # Mock the detected currencies
        detected_currencies = {
            'NIS_C_10': CurrencyInfo(quantity=2, return_currency_value=0.1),
            'EUR_C_5': CurrencyInfo(quantity=1, return_currency_value=0.05),
            'USD_C_50': CurrencyInfo(quantity=3, return_currency_value=0.5),
            'Unknown': CurrencyInfo(quantity=1, return_currency_value=0.0)
        }

        # Call the method under test
        updated_currencies = MyModel.calculate_return_currency_value(detected_currencies, 'USD')

        # Assertions
        assert updated_currencies['NIS_C_10'].return_currency_value == 0.03
        assert updated_currencies['EUR_C_5'].return_currency_value == 0.06
        assert updated_currencies['USD_C_50'].return_currency_value == 0.5
        assert updated_currencies['Unknown'].return_currency_value == 0.0

    def test_handle_unidentified_images(self, mocker):
        # Mock the YOLO model
        mock_yolo_model = mocker.Mock()
        
        # Mock Image conversion to raise UnidentifiedImageError
        mocker.patch("PIL.Image.fromarray", side_effect=UnidentifiedImageError)

        # Call the method under test with a dummy image
        cropped_images = [np.zeros((100, 100, 3), dtype=np.uint8)]  # Dummy image
        classified_objects = MyModel.classify_objects(mock_yolo_model, cropped_images)

        # Assertions
        assert classified_objects == [("Unknown", 0.0)]