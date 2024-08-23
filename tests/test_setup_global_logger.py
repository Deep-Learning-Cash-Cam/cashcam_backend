import pytest
import os
import logging
from app.logs.logger_config import setup_global_logger
from logging.handlers import RotatingFileHandler

class TestSetupGlobalLogger:
    @pytest.fixture
    def log_dir(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')

    # Logger is created successfully with the specified name 'cashcam'
    def test_logger_creation_with_name_cashcam(self, mocker):
        mock_get_logger = mocker.patch('logging.getLogger')
        mock_logger = mocker.Mock()
        mock_get_logger.return_value = mock_logger

        logger = setup_global_logger()

        mock_get_logger.assert_called_once_with('cashcam')
        assert logger == mock_logger

    # Log directory creation is called
    def test_log_directory_creation(self, mocker):
        mock_makedirs = mocker.patch('os.makedirs')

        setup_global_logger()

        mock_makedirs.assert_called_once()

    # Log messages are written to the file 'cashcam_log.log'
    def test_log_messages_written_to_file(self, mocker, log_dir):###
        mock_makedirs = mocker.patch('app.logs.logger_config.os.makedirs')
        mock_file_handler = mocker.patch('app.logs.logger_config.logging.handlers.RotatingFileHandler')
        mock_file_handler.return_value = mocker.Mock() 
        
        logger = setup_global_logger()

        mock_file_handler.assert_called_once_with(
            os.path.join(log_dir, 'cashcam_log.log'),
            maxBytes=10*1024*1024,
            backupCount=4
        )
        assert len(logger.handlers) > 0
        assert isinstance(logger.handlers[0], mocker.Mock)  # Ensure that the handler is a mock

    # Formatter is correctly applied to the log messages
    def test_formatter_correctly_applied(self, mocker):
        mock_formatter = mocker.patch('app.logs.logger_config.logging.Formatter')
        mock_file_handler = mocker.patch('app.logs.logger_config.RotatingFileHandler')
        mock_file_handler.return_value = mocker.Mock()  # Ensure it has return_value

        logger = setup_global_logger()

        mock_formatter.assert_called_once_with('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        mock_file_handler.return_value.setFormatter.assert_called_once_with(mock_formatter.return_value)

    # MaxBytes is set to 0 (no rollover)
    def test_maxbytes_set_to_zero(self, mocker, log_dir):###
        mock_file_handler = mocker.patch('app.logs.logger_config.logging.handlers.RotatingFileHandler')
        mock_file_handler.return_value = mocker.Mock()  # Ensure it has return_value

        setup_global_logger(max_bytes=0)

        mock_file_handler.assert_called_once_with(
            os.path.join(log_dir, 'cashcam_log.log'),
            maxBytes=0,
            backupCount=4
        )

    # BackupCount is set to 0 (no backup files)
    def test_backup_count_zero(self, mocker, log_dir):###
        mock_file_handler = mocker.patch('app.logs.logger_config.logging.handlers.RotatingFileHandler')
        mock_file_handler.return_value = mocker.Mock()  # Ensure it has return_value

        setup_global_logger(backup_count=0)

        mock_file_handler.assert_called_once_with(
            os.path.join(log_dir, 'cashcam_log.log'),
            maxBytes=10*1024*1024,
            backupCount=0
        )

    # Logger handles permission errors gracefully
    def test_permission_error_in_log_creation(self, mocker):
        mock_makedirs = mocker.patch('os.makedirs', side_effect=PermissionError)

        with pytest.raises(PermissionError):
            setup_global_logger()

    # Logger handles insufficient disk space
    def test_insufficient_disk_space_error(self, mocker):
        mock_makedirs = mocker.patch('os.makedirs', side_effect=OSError("No space left on device"))

        with pytest.raises(OSError):
            setup_global_logger()
