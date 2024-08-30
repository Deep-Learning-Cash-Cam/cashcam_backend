import pytest
import base64
import logging
import base64
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.api.endpoints.routes import predict
from app.schemas import PredictRequest
from app.schemas.predict_schema import CurrencyInfo
from app.schemas.user_schemas import User
from requests import Session
from io import BytesIO
from PIL import Image


@pytest.fixture
def mock_user():
    return User(id=1, email="test@example.com", name="Test User", role="admin")

@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)

@pytest.fixture
def valid_base64_image():
    image = Image.new('RGB', (100, 100), color='white')
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

class TestPredict:

    """Test valid base64 image is decoded and processed successfully."""
    @pytest.mark.asyncio
    async def test_valid_base64_image(self, mock_user, mock_db, valid_base64_image):
        request = PredictRequest(image=valid_base64_image, return_currency="USD")

        with patch('app.ml.model.MyModel.predict_image') as mock_predict_image, \
            patch('app.db.crud.save_image') as mock_save_image:
            # Mock the return values appropriately
            mock_predict_image.return_value = (MagicMock(), {"USD": CurrencyInfo(quantity=1, return_currency_value=1.0)})
            mock_save_image.return_value = "1"

            # Call the predict function
            response = await predict(request, mock_user, mock_db)

            # Assert the response
            assert response.currencies == {"USD": CurrencyInfo(quantity=1, return_currency_value=1.0)}
            assert response.image_id == "1"

    """Test invalid base64 image raises HTTP 400 error."""
    @pytest.mark.asyncio
    async def test_invalid_base64_image(self, mock_user, mock_db):
        invalid_base64_image = "invalid_base64"
        request = PredictRequest(image=invalid_base64_image, return_currency="USD")

        with pytest.raises(HTTPException) as exc_info:
            await predict(request, mock_user, mock_db)

        assert exc_info.value.status_code == 400
        assert "Invalid image - Unable to decode the image" in exc_info.value.detail

    """Test valid return currency is handled correctly."""
    @pytest.mark.asyncio
    async def test_valid_return_currency(self, mock_user, mock_db, valid_base64_image):
        request = PredictRequest(image=valid_base64_image, return_currency="USD")

        with patch('app.api.endpoints.routes.exchange_service') as mock_exchange_service, \
             patch('app.ml.model.MyModel.predict_image') as mock_predict_image, \
             patch('app.db.crud.save_image') as mock_save_image:
            mock_exchange_service.CURRENCIES = ["EUR", "USD", "ILS"]
            mock_predict_image.return_value = (MagicMock(), {"USD": CurrencyInfo(quantity=1, return_currency_value=1.0)})
            mock_save_image.return_value = "1"

            response = await predict(request, mock_user, mock_db)

            assert response.currencies == {"USD": CurrencyInfo(quantity=1, return_currency_value=1.0)}
            assert response.image_id == "1"

    """Test annotated image is encoded back to base64 successfully."""
    @pytest.mark.asyncio
    async def test_image_encoding_success(self, mock_user, mock_db, valid_base64_image):
        request = PredictRequest(image=valid_base64_image, return_currency="USD")

        with patch('app.ml.model.MyModel.predict_image') as mock_predict_image, \
             patch('app.db.crud.save_image') as mock_save_image:
            mock_predict_image.return_value = (MagicMock(), {"USD": CurrencyInfo(quantity=1, return_currency_value=1.0)})
            mock_save_image.return_value = "1"

            response = await predict(request, mock_user, mock_db)

            assert response.currencies == {"USD": CurrencyInfo(quantity=1, return_currency_value=1.0)}
            assert response.image_id == "1"

    """Test HTTP 400 response for prediction errors."""
    @pytest.mark.asyncio
    async def test_http_400_for_prediction_errors(self, valid_base64_image):
        request = PredictRequest(image=valid_base64_image, return_currency="USD")

        with patch('app.ml.model.MyModel.predict_image') as mock_predict_image, \
            patch('app.db.crud.save_image') as mock_save_image, \
            patch('app.api.endpoints.routes.log') as mock_log:
            mock_predict_image.side_effect = ValueError("Could not predict the image. Please try again later.")
            mock_save_image.return_value = "1"

            with pytest.raises(HTTPException) as exc_info:
                await predict(request, MagicMock(), MagicMock())

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "Could not predict the image. Please try again later."
            mock_log.assert_called_once_with("Error in prediction - Could not predict the image. Please try again later.", logging.ERROR)

    """Test invalid return currency raises HTTP 400."""
    @pytest.mark.asyncio
    async def test_invalid_return_currency_raises_value_error(self, valid_base64_image):
        invalid_currency = "XYZ"
        request = PredictRequest(image=valid_base64_image, return_currency=invalid_currency)

        with patch('app.api.endpoints.routes.exchange_service.CURRENCIES', ["EUR", "USD", "ILS"]), \
             patch('app.ml.model.MyModel.predict_image') as mock_predict_image:
            mock_predict_image.return_value = (MagicMock(), {"USD": CurrencyInfo(quantity=1, return_currency_value=1.0)})

            with pytest.raises(HTTPException) as exc_info:
                await predict(request, MagicMock(), MagicMock())

            assert exc_info.value.status_code == 400
            assert "Invalid return currency" in exc_info.value.detail
