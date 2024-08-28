import pytest

class TestPredict:

    # Test a valid base64 image that is processed successfully
    @pytest.mark.asyncio
    async def test_valid_base64_image(self, mocker):
        from app.api.endpoints.routes import predict
        from app.schemas import PredictRequest, PredictResponse
        from app.services.currency_exchange import exchange_service
        from app.ml.model import MyModel
        from PIL import Image
        import base64
        import io

        # Mock services
        mocker.patch.object(exchange_service, 'CURRENCIES', ["EUR", "USD", "ILS"])
        mocker.patch.object(MyModel, 'detect_and_collect_objects', return_value=([], []))
        mocker.patch.object(MyModel, 'classify_objects', return_value=[])
        mocker.patch.object(MyModel, 'annotate_image', return_value=Image.new('RGB', (100, 100)))
        mocker.patch.object(MyModel, 'get_detected_counts', return_value={})

        # Create valid base64 image
        image = Image.new('RGB', (100, 100))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode()

        request = PredictRequest(image=image_base64, return_currency="USD")

        # Execute the route
        response = await predict(request)

        # Assertions
        assert isinstance(response, PredictResponse)
        assert response.currencies == {}
        assert isinstance(response.image, str)

    # Test handling of invalid base64 string
    @pytest.mark.asyncio
    async def test_invalid_base64_image(self, mocker):
        from app.api.endpoints.routes import predict
        from app.schemas import PredictRequest
        from fastapi import HTTPException

        request = PredictRequest(image="invalid_base64", return_currency="USD")
    
        with pytest.raises(HTTPException) as exc_info:
            await predict(request)
    
        # Verify correct error response
        assert exc_info.value.status_code == 500
        assert "Invalid image - Unable to decode the image" in exc_info.value.detail

    # Test valid return currency conversion (e.g., "NIS" to "ILS")
    @pytest.mark.asyncio
    async def test_valid_return_currency_conversion(self, mocker):
        from app.api.endpoints.routes import predict
        from app.schemas import PredictRequest, PredictResponse
        from app.services.currency_exchange import exchange_service
        from app.ml.model import MyModel
        from PIL import Image
        import base64
        import io

        # Mock services
        mocker.patch.object(exchange_service, 'CURRENCIES', ["EUR", "USD", "ILS"])
        mocker.patch.object(MyModel, 'detect_and_collect_objects', return_value=([], []))
        mocker.patch.object(MyModel, 'classify_objects', return_value=[])
        mocker.patch.object(MyModel, 'annotate_image', return_value=Image.new('RGB', (100, 100)))
        mocker.patch.object(MyModel, 'get_detected_counts', return_value={})

        # Create valid base64 image
        image = Image.new('RGB', (100, 100))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode()

        request = PredictRequest(image=image_base64, return_currency="NIS")

        # Execute route
        response = await predict(request)

        # Check that the return_currency "NIS" is converted to "ILS"
        assert isinstance(response, PredictResponse)
        assert response.currencies == {}
        assert isinstance(response.image, str)

    # Test that an invalid return currency triggers a http exception
    @pytest.mark.asyncio
    async def test_invalid_return_currency_raises_http_exception(self, mocker):
        from app.api.endpoints.routes import predict
        from app.schemas import PredictRequest
        from fastapi import HTTPException

        # Prepare an invalid return currency request
        request = PredictRequest(image="dummy_base64_image", return_currency="JPY")

        # Verify the HTTPException for invalid currency
        with pytest.raises(HTTPException) as exc_info:
            await predict(request)

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal error - Invalid return currency"

    # Test that an empty image string raises a ValueError for an invalid image
    @pytest.mark.asyncio
    async def test_empty_image_string_raises_value_error(self, mocker):
        from app.api.endpoints.routes import predict
        from app.schemas import PredictRequest
        from fastapi import HTTPException

        # Mock the request with an empty image string
        request = PredictRequest(image="", return_currency="USD")

        # Check for a ValueError due to an empty image string
        with pytest.raises(HTTPException) as exc_info:
            await predict(request)

        assert exc_info.value.status_code == 500
        assert "Invalid image - Unable to decode the image" in exc_info.value.detail

    # Test that objects are detected and classified properly
    @pytest.mark.asyncio
    async def test_objects_detected_and_classified_successfully(self, mocker):
        from app.api.endpoints.routes import predict
        from app.schemas import PredictRequest, PredictResponse, CurrencyInfo
        from app.services.currency_exchange import exchange_service
        from app.ml.model import MyModel
        from PIL import Image
        import base64
        import io

        # Mock the services and models
        mocker.patch.object(exchange_service, 'CURRENCIES', ["EUR", "USD", "ILS"])
        mocker.patch.object(MyModel, 'detect_and_collect_objects', return_value=([Image.new('RGB', (100, 100))], ["ObjectClass"]))
        mocker.patch.object(MyModel, 'classify_objects', return_value=["ClassifiedObject"])
        mocker.patch.object(MyModel, 'annotate_image', return_value=Image.new('RGB', (100, 100)))
        mocker.patch.object(MyModel, 'get_detected_counts', return_value={
            "ClassifiedObject": CurrencyInfo(quantity=1, return_currency_value=10.0)
        })

        # Prepare valid base64 image
        image = Image.new('RGB', (100, 100))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode()

        request = PredictRequest(image=image_base64, return_currency="USD")

        # Execute the route
        response = await predict(request)

        # Validate the response
        assert isinstance(response, PredictResponse)
        assert response.currencies == {
            "ClassifiedObject": CurrencyInfo(quantity=1, return_currency_value=10.0)
        }
        assert isinstance(response.image, str)
