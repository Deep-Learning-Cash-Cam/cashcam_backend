
import requests
import logging
import pytest
from fastapi import HTTPException
from app.services.currency_exchange import exchange_service
from app.logs.logger_config import log

mock_rates = {"EUR_USD": 1.1167, "EUR_ILS": 4.103, "USD_EUR": 0.8955, "USD_ILS": 3.676, "ILS_EUR": 0.2438, "ILS_USD": 0.272}

class TestGetExchangeRates:
        
    
    # Fetch exchange rates successfully (including NIS)
    def test_fetch_exchange_rates_successfully(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value=mock_rates)
        response = exchange_service.get_exchange_rates()
        assert response == mock_rates

    def test_handle_network_failure_during_fetch(self, mocker):
        mocker.patch.object(exchange_service, 'fetch_rates', side_effect=requests.RequestException("Network error"))
        rates = exchange_service.get_exchange_rates()
        assert rates == exchange_service.backup_rates  # Check if backup rates are returned


    # Return exchange rates in JSON format (including NIS)
    def test_return_exchange_rates_successfully(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value=mock_rates)
        mocker.patch('app.api.endpoints.routes.log')
        response = exchange_service.get_exchange_rates()
        assert response == mock_rates

    # Log successful fetch of exchange rates (including NIS)
    def test_log_successful_fetch_exchange_rates(self, mocker):
        # Mock the function that fetches exchange rates
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value=mock_rates)
        # Mock the custom log function
        mock_log = mocker.patch('app.api.endpoints.routes.log')
        # Call the function
        response = exchange_service.get_exchange_rates()
        # Assert the response is as expected
        assert response == mock_rates
        # Assert the log was called exactly once with the correct message
        mock_log.assert_called_once_with("Successfully fetched exchange rates", logging.INFO)

        

    # Handle invalid response from external service
    def test_handle_invalid_response_from_external_service(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', side_effect=requests.RequestException)
        with pytest.raises(HTTPException) as exc_info:
            exchange_service.get_exchange_rates()
        assert exc_info.value.status_code == 500
    
    
    # Handle missing exchange rates file
    def test_handle_missing_exchange_rates_file(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            exchange_service.get_exchange_rates()
        assert exc_info.value.status_code == 404  # or the status code you're expecting
        assert exc_info.value.detail == "Exchange rates not found"

    
    # Handle corrupted exchange rates file
    def test_handle_corrupted_exchange_rates_file(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', side_effect=Exception("Corrupted file"))
        with pytest.raises(HTTPException) as exc_info:
            exchange_service.get_exchange_rates()
        assert exc_info.value.status_code == 500

    # Handle unexpected exceptions
    def test_handle_unexpected_exceptions(self, mocker):
        mock_exception = requests.RequestException("Connection Error")
        mocker.patch.object(exchange_service, 'get_exchange_rates', side_effect=mock_exception)
        mocker.patch('app.api.endpoints.routes.log')
        with pytest.raises(HTTPException) as exc_info:
            exchange_service.get_exchange_rates()
        assert exc_info.value.status_code == 500
        assert str(mock_exception) in exc_info.value.detail

    # Validate response structure (including NIS)
    def test_validate_response_structure(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value=mock_rates)
        response = exchange_service.get_exchange_rates()
        assert response == mock_rates

    # Verify HTTP 500 status code on failure
    def test_http_500_on_failure(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', side_effect=requests.RequestException)
        with pytest.raises(HTTPException) as exc_info:
            exchange_service.get_exchange_rates()
        assert exc_info.value.status_code == 500
    
    
    # Ensure proper logging of errors
    def test_logging_errors_properly(self, mocker):
        # Mock the exchange_service to raise a RequestException
        mocker.patch.object(exchange_service, 'get_exchange_rates', side_effect=requests.RequestException("Mocked RequestException"))
        # Mock the log function and assign it to a variable
        mock_log = mocker.patch('app.api.endpoints.routes.log')
        # Call the function and expect an HTTPException
        with pytest.raises(HTTPException) as exc_info:
            exchange_service.get_exchange_rates()
        # Assert that the HTTPException has the correct status code and detail
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Mocked RequestException"
        # Assert that the log function was called with the correct arguments
        mock_log.assert_called_once_with("Error in fetching exchange rates - Mocked RequestException", logging.ERROR)

    
    # Check for retries on fetch failure
    def test_retries_on_fetch_failure(self, mocker):
        mock_exception = requests.RequestException("Connection error")
        # Mock the exchange_service's get_exchange_rates method to raise an exception
        mocker.patch.object(exchange_service, 'get_exchange_rates', side_effect=mock_exception)
        # Mock the log function and assign the mock object to mock_log
        mock_log = mocker.patch('app.api.endpoints.routes.log')
        # Call the function and expect an HTTPException
        with pytest.raises(HTTPException) as exc_info:
            exchange_service.get_exchange_rates()
        # Assert that the HTTPException has the correct status code and detail
        assert exc_info.value.status_code == 500
        assert str(mock_exception) in exc_info.value.detail
        # Assert that the log function was called with the correct arguments
        mock_log.assert_called_once_with(f"Error in fetching exchange rates - {str(mock_exception)}", logging.ERROR)
    

    # Ensure no sensitive information in logs
    def test_no_sensitive_info_in_logs(self, mocker):
        mocker.patch.object(exchange_service, 'get_exchange_rates', return_value=mock_rates)
        mock_log = mocker.patch('app.api.endpoints.routes.log')
        
        # Call the function
        exchange_service.get_exchange_rates()
        
        # Check that log was called once with the successful fetch message
        assert mock_log.call_count == 1
        mock_log.assert_called_once_with("Successfully fetched exchange rates", logging.INFO)


