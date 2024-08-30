from unittest.mock import MagicMock
from jose import JWTError
import pytest
from fastapi import Request
from requests import Session
from app.api.dependencies import get_current_user
from app.db.crud import get_user
from app.core.security import verify_jwt_token
from app.schemas.user_schemas import User


@pytest.fixture
def mock_user():
    return User(id=1, email="test@example.com", name="Test User", role="admin")

@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)

class TestGetCurrentUser:

    # Test when user is found in request state
    @pytest.mark.asyncio
    async def test_user_in_request_state(self, mocker, mock_db):
        # Arrange: Mock request with user in state and mock DB
        mock_request = mocker.Mock(spec=Request)
        # Include both 'id' and 'email' in mock state user
        mock_request.state.user = {"id": 1, "email": "test@example.com"}
        #mock_db = mocker.Mock()

        # Mock get_user to return a user object
        mock_user = mocker.Mock()
        mocker.patch('app.db.crud.get_user', return_value=mock_user)

        # Act: Call the function
        user = await get_current_user(mock_request, mock_db)

        # Assert: Check if the correct user is returned and method called once
        assert user == mock_user
        get_user.assert_called_once_with(mock_db, user_id=1, email="test@example.com")


    # Test invalid token returns None
    @pytest.mark.asyncio
    async def test_invalid_token(self, mocker):   
        # Arrange: Mock request with invalid token and mock DB
        mock_request = mocker.Mock(spec=Request)
        mock_request.headers.get.return_value = "Bearer invalid_token"
        mock_db = mocker.Mock()

        # Mock verify_jwt_token to return None
        mocker.patch('app.core.security.verify_jwt_token', return_value=None)
    
        # Act: Call the function
        user = await get_current_user(mock_request, mock_db)
    
        # Assert: Ensure no user is returned, and the token was checked
        assert user is None
        verify_jwt_token.assert_called_once_with("invalid_token")

    # Test valid token returns user
    @pytest.mark.asyncio
    async def test_valid_token(self, mocker):
        # Arrange: Mock request with valid token, DB, and a user in DB
        mock_request = mocker.Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer valid_token"}
        mock_db = mocker.Mock()

        # Mock token verification to return payload
        mock_payload = {"sub": 1, "email": "test@example.com"}
        mocker.patch('app.core.security.verify_jwt_token', return_value=mock_payload)

        # Mock get_user to return a user
        mock_user = mocker.Mock()
        mocker.patch('app.db.crud.get_user', return_value=mock_user)

        # Act: Call the function
        user = await get_current_user(mock_request, mock_db)

        # Assert: Ensure the user is retrieved correctly, and methods are called as expected
        assert user == mock_user
        get_user.assert_called_once_with(mock_db, user_id=mock_payload["sub"], email=mock_payload["email"])

    # Test missing Authorization header
    @pytest.mark.asyncio
    async def test_missing_authorization_header(self, mocker):    
        # Arrange: Mock request without Authorization header and mock DB
        mock_request = mocker.Mock(spec=Request)
        mock_request.headers = {}
        mock_db = mocker.Mock()
    
        # Act: Call the function
        user = await get_current_user(mock_request, mock_db)
    
        # Assert: Ensure no user is returned
        assert user is None

    # Test token with missing fields returns None
    @pytest.mark.asyncio
    async def test_token_with_missing_fields(self, mocker):    
        # Arrange: Mock request with token missing fields, and mock DB
        mock_request = mocker.Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer valid_token"}
        mock_db = mocker.Mock()

        # Mock token verification to return a payload missing fields
        mocker.patch('app.core.security.verify_jwt_token', return_value={"sub": None, "email": None})
    
        # Act: Call the function
        user = await get_current_user(mock_request, mock_db)
    
        # Assert: Ensure no user is returned due to missing fields
        assert user is None

    # Test user not found in database
    @pytest.mark.asyncio
    async def test_user_not_found(self, mocker):    
        # Arrange: Mock request with valid token, mock DB, but no user in DB
        mock_request = mocker.Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer valid_token"}
        mock_db = mocker.Mock()

        # Mock token verification to return payload
        mock_payload = {"sub": 1, "email": "test@example.com"}
        mocker.patch('app.core.security.verify_jwt_token', return_value=mock_payload)

        # Mock get_user to return None
        mocker.patch('app.db.crud.get_user', return_value=None)

        # Act: Call the function
        user = await get_current_user(mock_request, mock_db)

        # Assert: Ensure no user is returned
        assert user is None
        get_user.assert_called_once_with(mock_db, user_id=1, email="test@example.com")

    # Test exception during token verification
    @pytest.mark.asyncio
    async def test_token_verification_exception(self, mocker):
        # Arrange: Mock request and mock DB, with exception on token verification
        mock_request = mocker.Mock(spec=Request)
        mock_db = mocker.Mock()

        # Mock verify_jwt_token to raise JWTError
        mocker.patch('app.core.security.verify_jwt_token', side_effect=JWTError)

        # Act: Call the function
        user = await get_current_user(mock_request, mock_db)

        # Assert: Ensure no user is returned
        assert user is None
