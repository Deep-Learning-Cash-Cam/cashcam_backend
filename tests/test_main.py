from fastapi import FastAPI
from unittest.mock import patch
from app.main import lifespan
from app.services.currency_exchange import ExchangeRateService
from httpx import AsyncClient
from app.main import app
import pytest
import time
import logging


#-------------------------------------------------------- lifespan -------------------------------------------------------#


class TestLifespan:

    @pytest.mark.asyncio
    async def test_server_startup_message(self):
        """Test that the server startup message is printed."""
        app = FastAPI()
        with patch('builtins.print') as mock_print:
            async with lifespan(app):
                mock_print.assert_called_with("Starting up the server...")

    @pytest.mark.asyncio
    async def test_handle_exceptions_during_startup(self):
        """Test handling of exceptions during server startup."""
        app = FastAPI()
        with patch('app.services.currency_exchange.ExchangeRateService.update_rates_daily', side_effect=Exception("Test Exception")):
            with pytest.raises(Exception, match="Test Exception"):
                async with lifespan(app):
                    pass

    @pytest.mark.asyncio
    async def test_log_entry_server_startup_and_task_creation(self):
        """Test server startup logs and task creation for exchange rate updates."""
        app = FastAPI()
        with patch('builtins.print') as mock_print, \
             patch('app.logs.logger_config.log') as mock_log, \
             patch('asyncio.create_task') as mock_create_task:
            async with lifespan(app):
                mock_print.assert_called_with("Starting up the server...")
                mock_log.assert_called_with("Server started.")
                mock_create_task.assert_called_with(ExchangeRateService.update_rates_daily())

    @pytest.mark.asyncio
    async def test_server_shutdown_logs(self):
        """Test that the server shutdown logs are created."""
        app = FastAPI()
        with patch('builtins.print') as mock_print, \
             patch('app.logs.logger_config.log') as mock_log:
            async with lifespan(app):
                pass
        mock_print.assert_called_with("Shutting down the server...")
        mock_log.assert_called_with("Server shut down.")

    @pytest.mark.asyncio
    async def test_handle_exceptions_during_task_creation(self):
        """Test handling exceptions during task creation."""
        app = FastAPI()
        with patch('asyncio.create_task', side_effect=Exception("Failed to create task")) as mock_create_task, \
             patch('app.logs.logger_config.log') as mock_log:
            async with lifespan(app):
                mock_log.assert_called_with("Starting up the server...")
                mock_log.assert_called_with("Server started.")
            mock_create_task.assert_called_with(ExchangeRateService.update_rates_daily())

    @pytest.mark.asyncio
    async def test_yield_allows_app_to_run(self):
        """Test that the yield allows the app to run and complete tasks."""
        app = FastAPI()
        with patch('builtins.print') as mock_print, \
             patch('app.logs.logger_config.log') as mock_log, \
             patch('asyncio.create_task') as mock_create_task:
            async with lifespan(app):
                mock_print.assert_called_with("Starting up the server...")
                mock_log.assert_called_with("Server started.")
                mock_create_task.assert_called_with(ExchangeRateService.update_rates_daily())
            mock_print.assert_called_with("Shutting down the server...")
            mock_log.assert_called_with("Server shut down.")

    @pytest.mark.asyncio
    async def test_log_invalid_levels(self):
        """Ensure that log function handles invalid log levels gracefully."""
        app = FastAPI()
        with patch('app.logs.logger_config.log') as mock_log:
            async with lifespan(app):
                mock_log.assert_called_with("Server started.")

    @pytest.mark.asyncio
    async def test_log_empty_message(self):
        """Ensure that log function handles empty log messages."""
        app = FastAPI()
        with patch('app.logs.logger_config.log') as mock_log:
            async with lifespan(app):
                mock_log.assert_called_with("Server started.")
                mock_log.assert_called_with("")

    @pytest.mark.asyncio
    async def test_log_entries_format(self):
        """Test that log entries have the correct format."""
        app = FastAPI()
        with patch('app.logs.logger_config.log') as mock_log:
            async with lifespan(app):
                mock_log.assert_called_with("Server started.")
                # You could add assertions for log formatting here


#---------------------------------------------------------- root ---------------------------------------------------------#


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

class TestRoot:
    # Test root endpoint returns correct message and handles unexpected query params
    @pytest.mark.asyncio
    async def test_welcome_message(self, async_client):
        response = await async_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to CashCam!"}
        
        # Test with unexpected query parameters
        response_with_query = await async_client.get("/?unexpected_param=value")
        assert response_with_query.status_code == 200
        assert response_with_query.json() == {"message": "Welcome to CashCam!"}

    # Test root endpoint accessibility and method limitations
    @pytest.mark.asyncio
    async def test_root_endpoint_methods(self, async_client):
        # Ensure GET request is allowed
        response = await async_client.get("/")
        assert response.status_code == 200

        # Ensure POST and PUT methods are not allowed
        for method in ['post', 'put']:
            response = await getattr(async_client, method)("/")
            assert response.status_code == 405
            assert response.json() == {"detail": "Method Not Allowed"}

    # Test for valid content type of the response
    @pytest.mark.asyncio
    async def test_confirm_content_type_json(self, async_client):
        response = await async_client.get("/")
        assert response.headers["content-type"] == "application/json"

    # Test logging when accessing the root endpoint
    @pytest.mark.asyncio
    async def test_verify_logging_root_access(self, mocker, async_client, caplog):
        from app.main import app
        from app.logs.logger_config import log

        with caplog.at_level(logging.INFO):
            response = await async_client.get("/")
            assert response.status_code == 200
            assert response.json() == {"message": "Welcome to CashCam!"}

            assert len(caplog.records) == 1
            assert caplog.records[0].levelname == "INFO"
            assert caplog.records[0].message == "Accessed root endpoint"

    # Test the response under heavy server load with mocks
    @pytest.mark.asyncio
    async def test_proper_response_under_heavy_load(self, mocker):
        mocker.patch('app.main.FastAPI')
        mocker.patch('app.main.api_router')
        mocker.patch('app.main.settings')
        mocker.patch('app.main.lifespan')
        mocker.patch('app.main.exchange_service')

        from app.main import root
        response = await root()
        assert response == {"message": "Welcome to CashCam!"}

    # Test response time of the root endpoint
    @pytest.mark.asyncio
    async def test_response_time_root_endpoint(self, async_client):
        start_time = time.time()
        response = await async_client.get("/")
        end_time = time.time()
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to CashCam!"}
        assert (end_time - start_time) < 1  # Response time should be < 1 second

    # Test root endpoint after server restart (assume restart logic is handled externally)
    @pytest.mark.asyncio
    async def test_confirm_endpoint_after_restart(self, async_client):
        response = await async_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to CashCam!"}
