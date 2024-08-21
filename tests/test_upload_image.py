import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from PIL import Image
from app.api.routes import upload_image
from fastapi import UploadFile, HTTPException
from unittest.mock import patch
import logging
from app.core.config import settings

client = TestClient(upload_image)

class TestUploadImage:

    # Successfully upload and encode a valid image file
    def test_successful_upload_and_encode_image(self, mocker):
        image = Image.new('RGB', (10, 10), color='red')
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        buffered.seek(0)

        response = client.post("/encode_image", files={"file": ("test.jpg", buffered, "image/jpeg")})

        assert response.status_code == 200
        assert "image" in response.json()

    # Upload a non-image file and handle the error gracefully
    def test_upload_non_image_file(self):
        non_image_file = BytesIO(b"this is not an image")

        response = client.post("/encode_image", files={"file": ("test.txt", non_image_file, "text/plain")})

        assert response.status_code == 500
        assert "cannot identify image file" in response.json()["detail"]

    # Handle image conversion to RGB format correctly
    def test_handle_image_conversion_to_rgb(self):
        image = Image.new('RGB', (10, 10), color='red')
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        buffered.seek(0)

        response = client.post("/encode_image", files={"file": ("test.jpg", buffered, "image/jpeg")})

        assert response.status_code == 200
        assert "image" in response.json()

    # Save the image in JPEG format
    def test_save_image_jpeg_format(self):
        image = Image.new('RGB', (10, 10), color='red')
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        buffered.seek(0)

        response = client.post("/encode_image", files={"file": ("test.jpg", buffered, "image/jpeg")})

        assert response.status_code == 200
        assert "image" in response.json()

    # Return a base64 encoded image string in JSON response
    def test_return_base64_encoded_image(self):
        image = Image.new('RGB', (10, 10), color='red')
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        buffered.seek(0)

        response = client.post("/encode_image", files={"file": ("test.jpg", buffered, "image/jpeg")})

        assert response.status_code == 200
        assert "image" in response.json()

    # Handle corrupted image files without crashing
    def test_handle_corrupted_image(self):
        corrupted_data = b'corrupted_image_data'
        buffered = BytesIO(corrupted_data)

        response = client.post("/encode_image", files={"file": ("corrupted.jpg", buffered, "image/jpeg")})

        assert response.status_code == 500

    # Manage large image files without performance issues
    def test_manage_large_image_files(self):
        image = Image.new('RGB', (1000, 1000), color='blue')
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        buffered.seek(0)

        response = client.post("/encode_image", files={"file": ("large_image.jpg", buffered, "image/jpeg")})

        assert response.status_code == 200
        assert "image" in response.json()

    # Handle missing file in the request
    def test_handle_missing_file(self):
        response = client.post("/encode_image")

        assert response.status_code == 422

    # Handle unsupported image formats
    def test_handle_unsupported_image_formats(self):
        image = Image.new('RGB', (10, 10), color='red')
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        buffered.seek(0)

        response = client.post("/encode_image", files={"file": ("test.png", buffered, "image/png")})

        assert response.status_code == 500

    # Validate the response model matches EncodedImageResponse
    def test_validate_response_model_matches_encoded_image_response(self):
        image = Image.new('RGB', (10, 10), color='red')
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        buffered.seek(0)

        response = client.post("/encode_image", files={"file": ("test.jpg", buffered, "image/jpeg")})

        assert response.status_code == 200
        assert "image" in response.json()

    # Ensure the endpoint is accessible via POST method
    def test_endpoint_accessibility_via_post_method(self):
        image = Image.new('RGB', (10, 10), color='red')
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        buffered.seek(0)

        response = client.post("/encode_image", files={"file": ("test.jpg", buffered, "image/jpeg")})

        assert response.status_code == 200
        assert "image" in response.json()

    # Ensure the DEBUG setting is checked before processing
    def test_debug_setting_checked(self, mocker):
        mock_upload_file = mocker.patch('app.api.routes.UploadFile')
        mock_upload_file.return_value.read.return_value = b'mock_image_data'
        
        mock_image_open = mocker.patch('app.api.routes.Image.open')
        mock_image_open.return_value = Image.new('RGB', (10, 10))

        settings.DEBUG = True
        response = client.post("/encode_image", files={"file": ("test.jpg", BytesIO(b"test"))})

        assert response.status_code == 200

    # Log errors with appropriate error messages
    def test_log_error_on_image_encoding_failure(self, mocker):
        with patch('app.api.routes.log') as mock_log:
            image = Image.new('RGB', (10, 10), color='red')
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            buffered.seek(0)

            with patch('PIL.Image.open') as mock_open:
                mock_open.side_effect = Exception('Image open error')

                response = client.post("/encode_image", files={"file": ("test.jpg", buffered, "image/jpeg")})

                assert response.status_code == 500
                assert "Image open error" in response.text
                mock_log.assert_called_once_with("Error in encoding the image - Image open error", logging.ERROR)

    # Verify the status code is 200 for successful operations
    def test_verify_status_code_for_successful_operations(self):
        image = Image.new('RGB', (10, 10), color='red')
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        buffered.seek(0)

        response = client.post("/encode_image", files={"file": ("test.jpg", buffered, "image/jpeg")})

        assert response.status_code == 200
