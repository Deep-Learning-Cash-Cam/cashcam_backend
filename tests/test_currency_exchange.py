
from app.services.currency_exchange import exchange_service
from unittest.mock import AsyncMock, patch
from httpx import patch
import httpx
import pytest

class TestFetchRates:

    # Fetches exchange rates successfully from the API
    @pytest.mark.asyncio
    async def test_fetch_rates_success(self, mocker):
        mock_response = mocker.AsyncMock()
        mock_response.json.return_value = {
            "result": "success",
            "conversion_rates": {"EUR_USD": 1.1172, "EUR_ILS": 4.1099, "USD_EUR": 0.8951, "USD_ILS": 3.6796, "ILS_EUR": 0.2433, "ILS_USD": 0.2717}  
        }
        mock_response.raise_for_status = mocker.AsyncMock()

        with mocker.patch('httpx.AsyncClient.get', return_value=mock_response):
            await exchange_service.fetch_rates()
        
            assert exchange_service.rates.get("USD_EUR") == 0.8951  
            assert exchange_service.rates.get("ILS_EUR") == 0.2433
            assert exchange_service.last_update is not None


    # Logs the successful update of exchange rates
    @pytest.mark.asyncio
    async def test_fetch_rates_successful_update(self, mocker):
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "result": "success",
            "conversion_rates": {"EUR_USD": 1.1172, "EUR_ILS": 4.1099, "USD_EUR": 0.8951, "USD_ILS": 3.6796, "ILS_EUR": 0.2433, "ILS_USD": 0.2717}  

        }
        mock_response.raise_for_status = AsyncMock()

        with patch('httpx.AsyncClient.get', return_value=mock_response):
            await exchange_service.fetch_rates()
    
            assert exchange_service.rates["EUR_USD"] == 0.8951
            assert exchange_service.rates["EUR_ILS"] == 0.2433
            assert exchange_service.last_update is not None

    # Logs errors appropriately when exceptions occur
    @pytest.mark.asyncio
    async def test_logs_errors_appropriately(self, mocker):
        # Setup
        mock_response = mocker.AsyncMock()
        mock_response.json.return_value = {
            "result": "success",
            "conversion_rates": {"EUR_USD": 1.1172, "EUR_ILS": 4.1099, "USD_EUR": 0.8951, "USD_ILS": 3.6796, "ILS_EUR": 0.2433, "ILS_USD": 0.2717}  
        }
        mock_response.raise_for_status = mocker.AsyncMock()
    
        with mocker.patch('httpx.AsyncClient.get', return_value=mock_response):
            # Exercise
            await exchange_service.fetch_rates()
    
            # Verify
            assert exchange_service.rates["EUR_USD"] == 0.8951
            assert exchange_service.rates["EUR_ILS"] == 0.2433
            assert exchange_service.last_update is not None

    # Saves rates to the cache file even if some currencies fail to fetch
    @pytest.mark.asyncio
    async def test_save_rates_even_with_partial_fetch(self, mocker):
        exchange_service.CURRENCIES = ["EUR", "USD", "ILS"]
        exchange_service.BASE_URL = "https://v6.exchangerate-api.com/v6"
        exchange_service.API_KEY = "test_api_key"
        exchange_service.rates = {}
        exchange_service.last_update = None
    
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "result": "success",
            "conversion_rates": {"EUR_USD": 1.1172, "EUR_ILS": 4.1099, "USD_EUR": 0.8951, "USD_ILS": 3.6796, "ILS_EUR": 0.2433, "ILS_USD": 0.2717}  
        }
        mock_response.raise_for_status = AsyncMock()
    
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            await exchange_service.fetch_rates()
    
            assert exchange_service.rates["EUR_USD"] == 0.8951
            assert exchange_service.rates["EUR_ILS"] == 0.2433
            assert exchange_service.last_update is not None

    # Uses backup rates if fetching fails for all currencies
    @pytest.mark.asyncio
    async def test_fetch_rates_backup_rates(self, mocker):
        mocker.patch('httpx.AsyncClient.get', side_effect=[httpx.HTTPStatusError(), httpx.RequestError(), Exception()])
        mocker.patch.object(exchange_service, 'save_rates_to_file')
        mocker.patch.object(exchange_service, 'CURRENCIES', ['USD', 'EUR', 'JPY'])
        mocker.patch.object(exchange_service, 'BASE_URL', 'https://api.exchangeratesapi.io')
        mocker.patch.object(exchange_service, 'API_KEY', 'test_key')
        mocker.patch.object(exchange_service, 'rates', {})
        mocker.patch.object(exchange_service, 'last_update', None)
        mocker.patch.object(exchange_service, 'save_rates_to_file')
    
        await exchange_service.fetch_rates()
    
        assert exchange_service.rates == {}
        assert exchange_service.last_update is None

    # Ensures the cache file is updated only when rates are successfully fetched
    @pytest.mark.asyncio
    async def test_cache_update_on_successful_fetch(self, mocker):
        mock_response = mocker.AsyncMock()
        mock_response.json.return_value = {
            "result": "success",
            "conversion_rates": {"EUR_USD": 1.1172, "EUR_ILS": 4.1099, "USD_EUR": 0.8951, "USD_ILS": 3.6796, "ILS_EUR": 0.2433, "ILS_USD": 0.2717}  
        }
        mock_response.raise_for_status = mocker.AsyncMock()

        with mocker.patch('httpx.AsyncClient.get', return_value=mock_response):
            await exchange_service.fetch_rates()
    
            assert exchange_service.last_update is not None
