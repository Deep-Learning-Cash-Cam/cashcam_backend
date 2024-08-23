import pytest
import logging
from app.logs.logger_config import log_message


@pytest.fixture
def logger():
    logger = logging.getLogger('test_logger')
    yield logger


class TestLogMessage:
    
    @pytest.mark.parametrize("level,message,expected_output", [
        ('DEBUG', 'This is a debug message', 'This is a debug message'),
        ('INFO', 'This is an info message', 'This is an info message'),
        ('WARNING', 'This is a warning message', 'This is a warning message'),
        ('ERROR', 'This is an error message', 'This is an error message'),
        ('CRITICAL', 'This is a critical message', 'This is a critical message'),
    ])
    def test_log_levels(self, logger, caplog, level, message, expected_output):
        logger.setLevel(logging.DEBUG)
        with caplog.at_level(getattr(logging, level)):
            log_message(logger, level, message)
            assert expected_output in caplog.text

    @pytest.mark.parametrize("level,expected_output", [
        ('UNKNOWN', "Unknown level 'UNKNOWN'"),
        ('', "Unknown level ''"),
        (None, "Unknown level 'None'"),
        ('SPECIAL!@#', "Unknown level 'SPECIAL!@#'"),
    ])
    def test_log_unknown_levels(self, logger, caplog, level, expected_output):
        logger.setLevel(logging.INFO)
        with caplog.at_level(logging.INFO):
            log_message(logger, level, 'Test message')
            assert expected_output in caplog.text

    def test_log_message_long_text(self, logger, caplog):
        logger.setLevel(logging.DEBUG)
        long_text = 'A' * 1000
        with caplog.at_level(logging.INFO):
            log_message(logger, 'INFO', long_text)
            assert long_text in caplog.text

    def test_log_message_multiline_text(self, logger, caplog):
        logger.setLevel(logging.DEBUG)
        multiline_message = 'This is a multiline message.\nIt spans across multiple lines.'
        with caplog.at_level(logging.INFO):
            log_message(logger, 'INFO', multiline_message)
            assert multiline_message in caplog.text

    @pytest.mark.parametrize("message,expected_output", [
        ('Special characters: !@#$%^&*()_+', 'Special characters: !@#$%^&*()_+'),
        (123, "123"),
        ('', ''),
    ])
    def test_log_message_special_cases(self, logger, caplog, message, expected_output):
        logger.setLevel(logging.DEBUG)
        with caplog.at_level(logging.INFO):
            log_message(logger, 'INFO', message)
            assert str(message) in caplog.text
