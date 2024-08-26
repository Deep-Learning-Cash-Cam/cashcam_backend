import pytest
from fastapi.testclient import TestClient
from app.schemas.request import EncodedImageRequest
from app.core.config import settings
from unittest.mock import patch
from fastapi import HTTPException
import logging
from app.main import app
from app.logs.logger_config import log  # Import the log function
from app.logs.logger_config import global_logger
client = TestClient(app)



# Successfully returns an HTML response with a valid base64 image string
def test_successful_html_response_with_base64_image():
    with patch.object(settings, 'DEBUG', True):
        img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
        request_data = EncodedImageRequest(image=img_str)

        response = client.post("/api/show_image", json=request_data.model_dump())  # Use model_dump for Pydantic v2

        assert response.status_code == 200
        assert "<img src=\"data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\"" in response.text

# Handles an invalid base64 image string
def test_handles_invalid_base64_image_string(mocker):
    mocker.patch.object(settings, 'DEBUG', True)
    img_str = "invalid_base64_string"
    request_data = EncodedImageRequest(image=img_str)
    
    # Optionally patch the log function, but ensure the level is an integer
    mock_log = mocker.patch("app.api.routes.log")
    
    # Make the POST request to the endpoint
    response = client.post("/api/show_image", json=request_data.model_dump())
    assert response.status_code == 500
    assert response.json() == {"detail": "Incorrect padding"}
    
    # Check that the log was called with the expected level (logging.ERROR, which is 40)
    mock_log.assert_called_once_with("Error in showing the image - Incorrect padding", logging.ERROR)



# Returns status code 200 for valid image input
def test_returns_status_code_200_for_valid_image_input(mocker):
    mocker.patch.object(settings, 'DEBUG', True)
    img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
    request_data = EncodedImageRequest(image=img_str)

    response = client.post("/api/show_image", json=request_data.model_dump())

    assert response.status_code == 200

# Processes a valid base64 image correctly
def test_correctly_processes_valid_base64_image(mocker):
    mocker.patch.object(settings, 'DEBUG', True)
    img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
    request_data = EncodedImageRequest(image=img_str)

    response = client.post("/api/show_image", json=request_data.model_dump())

    assert response.status_code == 200
    assert "<img src=\"data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\"" in response.text

# Returns HTTP 500 on general exception
def test_returns_http_500_on_exception(mocker):
    mocker.patch.object(settings, 'DEBUG', True)
    img_str = "invalid_base64_string"  # Intentionally invalid base64 string
    request_data = EncodedImageRequest(image=img_str)

    with patch('app.api.routes.log') as mock_log:
        response = client.post("/api/show_image", json=request_data.model_dump())
        
        assert response.status_code == 500

# Handles an empty image string
def test_handles_empty_image_string(mocker, caplog):
    # Mock settings.DEBUG to be True
    mocker.patch.object(settings, 'DEBUG', True)

    # Mock the logger's error method specifically
    mock_error = mocker.patch('app.logs.logger_config.global_logger.error')

    img_str = ""  # Empty base64 string
    request_data = EncodedImageRequest(image=img_str)

    # Perform the post request
    with caplog.at_level(logging.ERROR):
        response = client.post("/api/show_image", json=request_data.model_dump())

    # Ensure that the error method was called with the expected message
    mock_error.assert_called_with("Error in showing the image - Empty base64 string")




# Debug mode False, expect HTTP 200
def test_show_image_debug_false(mocker):
    mocker.patch.object(settings, 'DEBUG', False)
    img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
    request_data = EncodedImageRequest(image=img_str)

    response = client.post("/api/show_image", json=request_data.model_dump())

    assert response.status_code == 200  # Expecting 200 since the image is valid


# Logs error message correctly on exception
def test_logs_error_message_on_exception(mocker):
    mocker.patch.object(settings, 'DEBUG', True)
    # A valid base64 string that represents the beginning of a PNG image, but truncated
    #img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Truncated base64 string
    img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA==Invalid"  # Intentionally incorrect padding
    
    request_data = EncodedImageRequest(image=img_str)

    # Patch the log function in the correct module
    with patch('app.api.routes.log') as mock_log:
        response = client.post("/api/show_image", json=request_data.model_dump())

        # Check if the log was called with the expected error message
        mock_log.assert_called_once_with('Error in showing the image - Incorrect padding', logging.ERROR)
        assert response.status_code == 500

# Verifies valid base64 image tag presence in HTML response
def test_image_tag_presence_in_html_response(mocker):
    mocker.patch.object(settings, 'DEBUG', True)
    img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
    request_data = EncodedImageRequest(image=img_str)

    response = client.post("/api/show_image", json=request_data.model_dump())

    assert response.status_code == 200
    assert "<img src=\"data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\"" in response.text

# Validates the correct HTML structure in response
def test_correct_html_format(mocker):
    mocker.patch.object(settings, 'DEBUG', True)
    img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
    request_data = EncodedImageRequest(image=img_str)

    response = client.post("/api/show_image", json=request_data.model_dump())

    assert response.status_code == 200
    assert "<img src=\"data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\"" in response.text

# Ensures the content type of the response is HTML
def test_response_content_type_html(mocker):
    mocker.patch.object(settings, 'DEBUG', True)
    img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
    request_data = EncodedImageRequest(image=img_str)

    response = client.post("/api/show_image", json=request_data.model_dump())

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    
    
