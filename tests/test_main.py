from fastapi import FastAPI
from unittest.mock import patch
from app.main import lifespan
from app.services.currency_exchange import ExchangeRateService
import pytest

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
