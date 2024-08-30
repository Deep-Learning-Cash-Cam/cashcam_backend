import logging
import pytest
from fastapi import HTTPException
from app.api.endpoints.routes import get_image_history
from app.db import crud

class TestGetImageHistory:

    @pytest.mark.asyncio
    async def test_retrieves_image_history_for_valid_user(self, mocker):
        # Setup mocks
        mock_user = mocker.Mock()
        mock_user.id = 1
        mock_db = mocker.Mock()
        mock_images = ["image1", "image2"]

        # Patch methods
        mocker.patch.object(crud, 'get_images_by_user_id', return_value=mock_images)
        log_mock = mocker.patch('app.api.endpoints.routes.log', return_value=None)

        # Call function
        response = await get_image_history(mock_user, mock_db)

        # Assert response
        assert response == {"images": mock_images}

        # Adjust logging assertion if necessary
        log_mock.assert_called_once_with("Got image history for user: 1, logging.INFO", debug=True)

        
    @pytest.mark.asyncio
    async def test_user_not_found_raises_http_exception(self, mocker):
        # Setup mocks
        mock_user = None
        mock_db = mocker.Mock()

        # Call function and assert exception
        with pytest.raises(HTTPException) as exc_info:
            await get_image_history(mock_user, mock_db)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "User not found"

    @pytest.mark.asyncio
    async def test_logs_image_history_retrieval(self, mocker):
        # Setup mocks
        mock_user = mocker.Mock()
        mock_user.id = 1
        mock_db = mocker.Mock()
        mock_images = ["image1", "image2"]

        # Patch methods
        mocker.patch.object(crud, 'get_images_by_user_id', return_value=mock_images)
        log_mock = mocker.patch('app.api.endpoints.routes.log', return_value=None)

        # Call function
        await get_image_history(mock_user, mock_db)

        # Assert logging
        log_mock.assert_called_once_with(f"Got image history for user: {mock_user.id}, logging.INFO", debug=True)

    @pytest.mark.asyncio
    async def test_no_images_for_user(self, mocker):
        # Setup mocks
        mock_user = mocker.Mock()
        mock_user.id = 1
        mock_db = mocker.Mock()

        # Patch methods
        mocker.patch.object(crud, 'get_images_by_user_id', return_value=[])
        log_mock = mocker.patch('app.api.endpoints.routes.log', return_value=None)

        # Call function
        response = await get_image_history(mock_user, mock_db)

        # Assert response
        assert response == {"images": []}

    @pytest.mark.asyncio
    async def test_returns_error_message_on_exception(self, mocker):
        # Setup mocks
        mock_user = mocker.Mock()
        mock_user.id = 1
        mock_db = mocker.Mock()

        # Patch methods
        mocker.patch.object(crud, 'get_images_by_user_id', side_effect=Exception("Database connection error"))
        log_mock = mocker.patch('app.api.endpoints.routes.log', return_value=None)

        # Call function
        response = await get_image_history(mock_user, mock_db)

        # Assert response
        assert response == {"message": "Error in getting image history"}
        log_mock.assert_called_once_with(f"Error in getting image history for user: {mock_user.id} - Database connection error", logging.ERROR)

    @pytest.mark.asyncio
    async def test_logging_respects_debug_flag(self, mocker):
        # Setup mocks
        mock_user = mocker.Mock()
        mock_user.id = 1
        mock_db = mocker.Mock()
        mock_images = ["image1", "image2"]

        # Patch methods
        mocker.patch.object(crud, 'get_images_by_user_id', return_value=mock_images)
        log_mock = mocker.patch('app.api.endpoints.routes.log', return_value=None)

        # Call function
        response = await get_image_history(mock_user, mock_db)

        # Assert logging respects debug flag
        log_mock.assert_called_once_with(f"Got image history for user: {mock_user.id}, logging.INFO", debug=True)
        assert response == {"images": mock_images}

    @pytest.mark.asyncio
    async def test_valid_user_dependency_injection(self, mocker):
        # Setup mocks
        mock_user = mocker.Mock()
        mock_user.id = 1
        mock_db = mocker.Mock()
        mock_images = ["image1", "image2"]

        # Patch methods
        mocker.patch.object(crud, 'get_images_by_user_id', return_value=mock_images)

        # Call function
        response = await get_image_history(mock_user, mock_db)

        # Assert response
        assert response == {"images": mock_images}

    @pytest.mark.asyncio
    async def test_valid_db_dependency_injection(self, mocker):
        # Setup mocks
        mock_user = mocker.Mock()
        mock_user.id = 1
        mock_db = mocker.Mock()
        mock_images = ["image1", "image2"]

        # Patch methods
        mocker.patch.object(crud, 'get_images_by_user_id', return_value=mock_images)

        # Call function
        response = await get_image_history(mock_user, mock_db)

        # Assert response
        assert response == {"images": mock_images}
