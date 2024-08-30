import pytest
from fastapi import HTTPException
from app.api.endpoints.routes import get_rates
from app.services.currency_exchange import exchange_service
from app.schemas.user_schemas import User
from requests import RequestException
import logging


class TestGetRates:

    @pytest.fixture
    def mock_admin_user(self):
        return User(id=1, email="test@example.com", name="Test User", role="admin")

    @pytest.fixture
    def mock_non_admin_user(self):
        return User(id=1, email="test@example.com", name="Test User", role="pass")

    @pytest.fixture
    def mock_db(self, mocker):
        return mocker.Mock()

    @pytest.fixture
    def mock_rates(self):
        return {"EUR_USD": 1.1172, "EUR_ILS": 4.1099, "USD_EUR": 0.8951, "USD_ILS": 3.6796, "ILS_EUR": 0.2433, "ILS_USD": 0.2717}

    def test_admin_user_retrieves_exchange_rates(self, mock_admin_user, mock_db, mock_rates, mocker):
        # Mock the exchange_service.get_exchange_rates method
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value=mock_rates)

        # Call the function
        response = get_rates(mock_admin_user, mock_db)

        # Assert the response
        assert response == {"exchange_rates": mock_rates}

    def test_non_admin_user_receives_401_error(self, mock_non_admin_user, mock_db):
        # Call the function and assert it raises HTTPException with status code 401
        with pytest.raises(HTTPException) as exc_info:
            get_rates(mock_non_admin_user, mock_db)

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "401: Unauthorized"

    def test_request_exception_handling(self, mock_admin_user, mock_db, mocker):
        # Mock the exchange_service.get_exchange_rates method to raise an exception
        mock_exception = RequestException("Connection error")
        mocker.patch.object(exchange_service, 'get_exchange_rates', side_effect=mock_exception)

        # Mock the log function
        log = mocker.patch("app.api.endpoints.routes.log")

        # Call the function and assert the correct behavior
        with pytest.raises(HTTPException) as exc_info:
            get_rates(mock_admin_user, mock_db)

        # Assert the log function was called with the correct message and logging level
        log.assert_called_once_with("Error in fetching exchange rates - Connection error", logging.ERROR)


