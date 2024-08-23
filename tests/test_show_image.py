import pytest
from fastapi.testclient import TestClient
from app.schemas.request import EncodedImageRequest
from app.core.config import settings
from unittest.mock import patch
from fastapi import HTTPException
import logging
from app.main import app

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

    response = client.post("/api/show_image", json=request_data.dict())

    assert response.status_code == 500
    assert response.json() == {"detail": "Incorrect padding"}


# Returns status code 200 for valid image input
def test_returns_status_code_200_for_valid_image_input(mocker):
    mocker.patch.object(settings, 'DEBUG', True)
    img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
    request_data = EncodedImageRequest(image=img_str)

    response = client.post("/api/show_image", json=request_data.dict())

    assert response.status_code == 200

# Processes a valid base64 image correctly
def test_correctly_processes_valid_base64_image(mocker):
    mocker.patch.object(settings, 'DEBUG', True)
    img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
    request_data = EncodedImageRequest(image=img_str)

    response = client.post("/api/show_image", json=request_data.dict())

    assert response.status_code == 200
    assert "<img src=\"data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\"" in response.text

# Returns HTTP 500 on general exception##########################################
def test_returns_http_500_on_exception(mocker):
    mocker.patch.object(settings, 'DEBUG', True)
    img_str = "invalid_base64_string"  # Intentionally invalid base64 string
    request_data = EncodedImageRequest(image=img_str)

    with patch('app.api.routes.log') as mock_log:
        response = client.post("/api/show_image", json=request_data.dict())
        
        assert response.status_code == 500

# Handles an empty image string
def test_handles_empty_image_string(mocker):
    mocker.patch.object(settings, 'DEBUG', True)
    img_str = ""  # Empty base64 string
    request_data = EncodedImageRequest(image=img_str)

    response = client.post("/api/show_image", json=request_data.dict())

    assert response.status_code == 500

# Debug mode False, expect HTTP 200
def test_show_image_debug_false(mocker):
    mocker.patch.object(settings, 'DEBUG', False)
    img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
    request_data = EncodedImageRequest(image=img_str)

    response = client.post("/api/show_image", json=request_data.dict())

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
        response = client.post("/api/show_image", json=request_data.dict())

        # Check if the log was called with the expected error message
        mock_log.assert_called_once_with('Error in showing the image - Incorrect padding', logging.ERROR)
        assert response.status_code == 500

# Verifies valid base64 image tag presence in HTML response
def test_image_tag_presence_in_html_response(mocker):
    mocker.patch.object(settings, 'DEBUG', True)
    img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
    request_data = EncodedImageRequest(image=img_str)

    response = client.post("/api/show_image", json=request_data.dict())

    assert response.status_code == 200
    assert "<img src=\"data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\"" in response.text

# Validates the correct HTML structure in response
def test_correct_html_format(mocker):
    mocker.patch.object(settings, 'DEBUG', True)
    img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
    request_data = EncodedImageRequest(image=img_str)

    response = client.post("/api/show_image", json=request_data.dict())

    assert response.status_code == 200
    assert "<img src=\"data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\"" in response.text

# Ensures the content type of the response is HTML
def test_response_content_type_html(mocker):
    mocker.patch.object(settings, 'DEBUG', True)
    img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
    request_data = EncodedImageRequest(image=img_str)

    response = client.post("/api/show_image", json=request_data.dict())

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    
    
