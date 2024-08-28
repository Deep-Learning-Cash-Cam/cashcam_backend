import pytest
import os
import logging
from app.logs.logger_config import setup_global_logger

"""

Copy your path to the failed tests so make them work. The path will be printed after the test's failure summery. 

Paths to our local loggers:

Uri - 'C:\\Users\\Uri Beeri\\Computer Science\\final-project-deep-learning\\app\\logs\\..\\logs\\cashcam_log.log'
Itay - Add yours here
Yuval - Add yours here
Daniel - Add yours here
Ron - Add yours here

"""

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
    def test_log_messages_written_to_file(self, mocker):
        mock_makedirs = mocker.patch('app.logs.logger_config.os.makedirs')
        
        # Set up a real file path (the regular logger file) --> Change it to your own path
        log_file_path = 'C:\\Users\\Uri Beeri\\Computer Science\\final-project-deep-learning\\app\\logs\\..\\logs\\cashcam_log.log'

        # Create a real logger, but mock the file handler
        mock_file_handler = mocker.patch('app.logs.logger_config.RotatingFileHandler', wraps=logging.handlers.RotatingFileHandler)
        
        # Call the function to set up the logger with the real file path
        logger = setup_global_logger()
        
        # Verify the logger is set up to write to the correct file path
        mock_file_handler.assert_called_once_with(
            log_file_path,
            maxBytes=10*1024*1024,
            backupCount=4
        )
        
        # Log a message
        logger.info("This is a test log message")
        
        # Flush the logger's handlers to ensure all log messages are written
        for handler in logger.handlers:
            handler.flush()
        
        # Verify the log file contains the expected message
        with open(log_file_path, 'r') as log_file:
            log_content = log_file.read()
        
        assert "This is a test log message" in log_content

    # Formatter is correctly applied to the log messages
    def test_formatter_correctly_applied(self, mocker):
        mock_formatter = mocker.patch('app.logs.logger_config.logging.Formatter')
        mock_file_handler = mocker.patch('app.logs.logger_config.RotatingFileHandler')
        mock_file_handler.return_value = mocker.Mock()  # Ensure it has return_value

        logger = setup_global_logger()

        mock_formatter.assert_called_once_with('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        mock_file_handler.return_value.setFormatter.assert_called_once_with(mock_formatter.return_value)

    # MaxBytes is set to 0 (no rollover)
    def test_maxbytes_set_to_zero(self, mocker, log_dir):
        mock_file_handler = mocker.patch('app.logs.logger_config.RotatingFileHandler')
        mock_file_handler.return_value = mocker.Mock()  # Ensure it has return_value

        setup_global_logger(maxBytes=0)

        # Change it to your own path
        log_dir = 'C:\\Users\\Uri Beeri\\Computer Science\\final-project-deep-learning\\app\\logs\\..\\logs\\cashcam_log.log'
        mock_file_handler.assert_called_once_with(
            log_dir,
            maxBytes=0,
            backupCount=4
        )

    # BackupCount is set to 0 (no backup files)
    def test_backup_count_zero(self, mocker, log_dir):
        mock_file_handler = mocker.patch('app.logs.logger_config.RotatingFileHandler')
        mock_file_handler.return_value = mocker.Mock()  # Ensure it has return_value

        setup_global_logger(backupCount=0)

        # Change it to your own path
        log_dir = 'C:\\Users\\Uri Beeri\\Computer Science\\final-project-deep-learning\\app\\logs\\..\\logs\\cashcam_log.log'
        mock_file_handler.assert_called_once_with(
            log_dir,
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
