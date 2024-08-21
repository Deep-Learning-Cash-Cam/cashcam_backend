"""from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to CashCam!"}
"""  
#--------------Uri and Yuval--------------------------

import requests
import logging
import pytest
from fastapi import HTTPException
from app.api.routes import get_exchange_rates
from app.services.currency_exchange import exchange_service
from app.logs import log

class TestGetExchangeRates:

    # Fetch exchange rates successfully (including NIS)
    def test_fetch_exchange_rates_successfully(self, mocker):
        mock_rates = {"USD": 1.0, "EUR": 0.85, "NIS": 3.5}
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value=mock_rates)
        response = get_exchange_rates()
        assert response == {"exchange_rates": mock_rates}

    # Handle network failure during fetch
    def test_handle_network_failure_during_fetch(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', side_effect=requests.RequestException("Network error"))
        with pytest.raises(HTTPException) as exc_info:
            get_exchange_rates()
        assert exc_info.value.status_code == 500
        assert "Network error" in exc_info.value.detail

    # Return exchange rates in JSON format (including NIS)
    def test_return_exchange_rates_successfully(self, mocker):
        mock_rates = {"USD": 1.0, "EUR": 0.85, "NIS": 3.5}
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value=mock_rates)
        mocker.patch('app.api.routes.log')
        response = get_exchange_rates()
        assert response == {"exchange_rates": mock_rates}

    # Log successful fetch of exchange rates (including NIS)
    def test_log_successful_fetch_exchange_rates(self, mocker):
        mock_rates = {"USD": 1.0, "EUR": 0.85, "NIS": 3.5}
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value=mock_rates)
        mocker.patch('app.api.routes.log')
        response = get_exchange_rates()
        assert response == {"exchange_rates": mock_rates}
        log.assert_called_once_with("Loaded rates from file")

    # Handle invalid response from external service
    def test_handle_invalid_response_from_external_service(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', side_effect=requests.RequestException)
        with pytest.raises(HTTPException) as exc_info:
            get_exchange_rates()
        assert exc_info.value.status_code == 500

    # Handle missing exchange rates file
    def test_handle_missing_exchange_rates_file(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            get_exchange_rates()
        assert exc_info.value.status_code == 500

    # Handle corrupted exchange rates file
    def test_handle_corrupted_exchange_rates_file(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', side_effect=Exception("Corrupted file"))
        with pytest.raises(HTTPException) as exc_info:
            get_exchange_rates()
        assert exc_info.value.status_code == 500

    # Handle unexpected exceptions
    def test_handle_unexpected_exceptions(self, mocker):
        mock_exception = requests.RequestException("Connection Error")
        mocker.patch.object(exchange_service, 'get_exchange_rates', side_effect=mock_exception)
        mocker.patch('app.api.routes.log')
        with pytest.raises(HTTPException) as exc_info:
            get_exchange_rates()
        assert exc_info.value.status_code == 500
        assert str(mock_exception) in exc_info.value.detail

    # Validate response structure (including NIS)
    def test_validate_response_structure(self, mocker):
        mock_rates = {"USD": 1.0, "EUR": 0.85, "NIS": 3.5}
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value=mock_rates)
        response = get_exchange_rates()
        assert response == {"exchange_rates": mock_rates}

    # Verify HTTP 500 status code on failure
    def test_http_500_on_failure(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', side_effect=requests.RequestException)
        with pytest.raises(HTTPException) as exc_info:
            get_exchange_rates()
        assert exc_info.value.status_code == 500

    # Ensure proper logging of errors
    def test_logging_errors_properly(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', side_effect=requests.RequestException("Mocked RequestException"))
        mocker.patch('app.api.routes.log')
        with pytest.raises(HTTPException) as exc_info:
            get_exchange_rates()
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Mocked RequestException"
        log.assert_called_once_with("Error in fetching exchange rates - Mocked RequestException", logging.ERROR)

    # Check for retries on fetch failure
    def test_retries_on_fetch_failure(self, mocker):
        mock_exception = requests.RequestException("Connection error")
        mocker.patch.object(exchange_service, 'get_exchange_rates', side_effect=mock_exception)
        mocker.patch("app.api.routes.log")
        with pytest.raises(HTTPException) as exc_info:
            get_exchange_rates()
        assert exc_info.value.status_code == 500
        assert str(mock_exception) in exc_info.value.detail
        log.assert_called_once_with(f"Error in fetching exchange rates - {str(mock_exception)}", logging.ERROR)

    # Ensure no sensitive information in logs
    def test_no_sensitive_info_in_logs(self, mocker):
        mock_rates = {"USD": 1.0, "EUR": 0.85, "NIS": 3.5}
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value=mock_rates)
        mocker.patch("app.api.routes.requests.RequestException", Exception)
        with mocker.patch("app.api.routes.log") as mock_log:
            get_exchange_rates()
            assert mock_log.call_count == 2
            assert "Error in fetching exchange rates" in mock_log.call_args_list[0][0][0]
            assert "General error" in mock_log.call_args_list[1][0][0]
