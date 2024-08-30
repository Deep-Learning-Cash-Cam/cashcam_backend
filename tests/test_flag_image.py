from app.api.endpoints.routes import flag_image
from fastapi import HTTPException
from requests import patch
import pytest

class TestFlagImage:

    # Successfully flagging an image when user is authenticated and image exists
    @pytest.mark.asyncio
    async def test_flag_image_success(self, mocker):
        mock_user = mocker.Mock()
        mock_user.id = 1
        mock_db = mocker.Mock()
        mocker.patch("app.db.crud.flag_image", return_value=True)

        response = await flag_image(user=mock_user, db=mock_db, image_id=1)

        assert response == {"message": "Image flagged successfully"}

    # Handling the case where the user is not authenticated
    @pytest.mark.asyncio
    async def test_flag_image_unauthenticated(self, mocker):
        mock_user = None
        mock_db = mocker.Mock()

        with pytest.raises(HTTPException) as exc_info:
            await flag_image(user=mock_user, db=mock_db, image_id=1)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "User not found - Unauthorized"

    # Handling unexpected exceptions during the flagging process
    @pytest.mark.asyncio
    async def test_handling_unexpected_exceptions(self, mocker):
        mock_user = mocker.Mock()
        mock_user.id = 1
        mock_db = mocker.Mock()
        mocker.patch("app.db.crud.flag_image", side_effect=Exception("Test Exception"))

        response = await flag_image(user=mock_user, db=mock_db, image_id=1)

        assert response == {"message": "Error in flagging the image"}

    # Handling the case where the image does not exist or is already flagged
    @pytest.mark.asyncio
    async def test_flag_image_image_not_found_or_already_flagged(self, mocker):
        mock_user = mocker.Mock()
        mock_user.id = 1
        mock_db = mocker.Mock()
        mocker.patch("app.db.crud.flag_image", return_value=False)

        response = await flag_image(user=mock_user, db=mock_db, image_id=1)

        assert response == {"message": "Image not found or already flagged"}

    # Ensuring the database commit occurs only when the image is flagged
    @pytest.mark.asyncio
    async def test_flag_image_commit(self, mocker):
        mock_user = mocker.Mock()
        mock_user.id = 1
        mock_db = mocker.Mock()
        mock_flag_image = mocker.patch("app.db.crud.flag_image", return_value=True)

        response = await flag_image(user=mock_user, db=mock_db, image_id=1)

        assert response == {"message": "Image flagged successfully"}
        mock_flag_image.assert_called_once_with(mock_db, mock_user.id, 1)

        