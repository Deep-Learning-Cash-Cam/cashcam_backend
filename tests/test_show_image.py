import pytest
from fastapi.testclient import TestClient
from app.api.routes import show_image
from app.schemas.request import EncodedImageRequest
from app.core.config import settings
from fastapi import HTTPException
import logging
from unittest.mock import patch

client = TestClient(show_image)

class TestShowImage:

    # Successfully returns an HTML response with a valid base64 image string
    def test_successful_html_response_with_base64_image(self, mocker):
        mocker.patch.object(settings, 'DEBUG', True)
        img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
        request_data = EncodedImageRequest(image=img_str)

        response = client.post("/show_image", json=request_data.dict())

        assert response.status_code == 200
        assert "<img src=\"data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\"" in response.text

    # Handles an invalid base64 image string
    def test_handles_invalid_base64_image_string(self, mocker):
        mocker.patch.object(settings, 'DEBUG', True)
        img_str = "invalid_base64_string"
        request_data = EncodedImageRequest(image=img_str)

        response = client.post("/show_image", json=request_data.dict())

        assert response.status_code == 500
        assert response.json() == {"detail": "Error in showing the image - Incorrect padding"}

    # Returns status code 200 for valid image input
    def test_returns_status_code_200_for_valid_image_input(self, mocker):
        mocker.patch.object(settings, 'DEBUG', True)
        img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
        request_data = EncodedImageRequest(image=img_str)

        response = client.post("/show_image", json=request_data.dict())

        assert response.status_code == 200

    # Processes a valid base64 image correctly
    def test_correctly_processes_valid_base64_image(self, mocker):
        mocker.patch.object(settings, 'DEBUG', True)
        img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
        request_data = EncodedImageRequest(image=img_str)

        response = client.post("/show_image", json=request_data.dict())

        assert response.status_code == 200
        assert "<img src=\"data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\"" in response.text

    # Returns HTTP 500 on general exception
    def test_returns_http_500_on_exception(self, mocker):
        mocker.patch.object(settings, 'DEBUG', True)
        img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
        request_data = EncodedImageRequest(image=img_str)

        with patch('app.api.routes.log') as mock_log:
            mock_log.side_effect = Exception("Test Exception")
            response = client.post("/show_image", json=request_data.dict())
        
            assert response.status_code == 500

    # Handles an empty image string
    def test_handles_empty_image_string(self, mocker):
        mocker.patch.object(settings, 'DEBUG', True)
        img_str = ""  # Empty base64 string
        request_data = EncodedImageRequest(image=img_str)

        response = client.post("/show_image", json=request_data.dict())

        assert response.status_code == 500

    # Debug mode False test, expect HTTP 500
    def test_show_image_debug_false(self, mocker):
        mocker.patch.object(settings, 'DEBUG', False)
        img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
        request_data = EncodedImageRequest(image=img_str)

        response = client.post("/show_image", json=request_data.dict())

        assert response.status_code == 500

    # Logs error message correctly on exception
    def test_logs_error_message_on_exception(self, mocker):
        mocker.patch.object(settings, 'DEBUG', True)
        img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
        request_data = EncodedImageRequest(image=img_str)

        with patch('app.api.routes.log') as mock_log:
            response = client.post("/show_image", json=request_data.dict())
        
            mock_log.assert_called_once_with('Error in showing the image - Incorrect padding', logging.ERROR)
            assert response.status_code == 500

    # Verifies valid base64 image tag presence in HTML response
    def test_image_tag_presence_in_html_response(self, mocker):
        mocker.patch.object(settings, 'DEBUG', True)
        img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
        request_data = EncodedImageRequest(image=img_str)

        response = client.post("/show_image", json=request_data.dict())

        assert response.status_code == 200
        assert "<img src=\"data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\"" in response.text

    # Validates the correct HTML structure in response
    def test_correct_html_format(self, mocker):
        mocker.patch.object(settings, 'DEBUG', True)
        img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
        request_data = EncodedImageRequest(image=img_str)

        response = client.post("/show_image", json=request_data.dict())

        assert response.status_code == 200
        assert "<img src=\"data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\"" in response.text

    # Ensures the content type of the response is HTML
    def test_response_content_type_html(self, mocker):
        mocker.patch.object(settings, 'DEBUG', True)
        img_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA"  # Example base64 string
        request_data = EncodedImageRequest(image=img_str)

        response = client.post("/show_image", json=request_data.dict())

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
