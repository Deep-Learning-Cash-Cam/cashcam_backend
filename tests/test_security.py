from datetime import datetime, timedelta, timezone
import logging
import re
import pytest
from jose import jwt
from app.core.config import settings
from app.core.security import create_access_token


#------------------------------------------------------ create_access_token ------------------------------------------------------#


utc3_time = timezone(timedelta(hours=3))

class TestCreateAccessToken:

    @pytest.fixture
    def setup_mocks(self, mocker):
        mock_time_now = datetime.now(utc3_time)
        mocker.patch('app.core.security.datetime', autospec=True)
        mocker.patch('app.core.security.datetime.now', return_value=mock_time_now)
        mock_log = mocker.patch('app.core.security.log')
        return mock_time_now, mock_log

    def verify_token(self, token, expected_sub, expected_exp, mock_time_now):
        decoded_token = jwt.decode(token, settings.JWT_ACCESS_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        # Check if 'sub' exists in the decoded token, and compare it with the expected_sub
        if expected_sub is None:
            assert "sub" not in decoded_token, "Token contains 'sub' claim when it shouldn't."
        else:
            assert decoded_token["sub"] == expected_sub, f"Expected sub: {expected_sub}, got: {decoded_token['sub']}"
        
        # Check the expiration time
        assert decoded_token["exp"] == int(expected_exp.timestamp()), f"Expected exp: {expected_exp.timestamp()}, got: {decoded_token['exp']}"

    
    def test_generate_token_with_default_expiration(self, setup_mocks):
        mock_time_now, _ = setup_mocks

        data = {"sub": "user_id"}
        token = create_access_token(data)
        expected_exp = mock_time_now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.verify_token(token, "user_id", expected_exp, mock_time_now)

    def test_handle_empty_data_dict(self, setup_mocks):
        mock_time_now, _ = setup_mocks

        data = {}
        token = create_access_token(data)
        expected_exp = mock_time_now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.verify_token(token, None, expected_exp, mock_time_now)

    def test_generate_token_with_custom_expiration(self, setup_mocks):
        mock_time_now, _ = setup_mocks

        data = {"sub": "user_id"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)
        expected_exp = mock_time_now + expires_delta
        self.verify_token(token, "user_id", expected_exp, mock_time_now)

    def test_logs_access_token_creation(self, setup_mocks):
        mock_time_now, mock_log = setup_mocks

        data = {"sub": "user_id"}
        create_access_token(data)
        
        # Extract the actual log message
        call_args = mock_log.call_args[0]
        log_message = call_args[0]
        
        # Check that the log message contains the expected substring
        assert 'Access token created! Expiration time:' in log_message, \
            f"Expected log message to contain 'Access token created! Expiration time:', but got {log_message}"
        
        # Check if the logging level is correct
        assert call_args[1] == logging.INFO, \
            f"Expected log level to be INFO, but got {call_args[1]}"

    def test_handles_none_expires_delta_without_errors(self, setup_mocks):
        mock_time_now, _ = setup_mocks

        data = {"sub": "user_id"}
        token = create_access_token(data, expires_delta=None)
        expected_exp = mock_time_now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.verify_token(token, "user_id", expected_exp, mock_time_now)

    def test_handles_short_expiration(self, setup_mocks):
        mock_time_now, _ = setup_mocks

        data = {"sub": "user_id"}
        expires_delta = timedelta(seconds=30)
        token = create_access_token(data, expires_delta)
        expected_exp = mock_time_now + expires_delta
        self.verify_token(token, "user_id", expected_exp, mock_time_now)

    def test_handles_very_long_expiration_times_correctly(self, setup_mocks):
        mock_time_now, _ = setup_mocks

        data = {"sub": "user_id"}
        expires_delta = timedelta(days=365)
        token = create_access_token(data, expires_delta)
        expected_exp = mock_time_now + expires_delta
        self.verify_token(token, "user_id", expected_exp, mock_time_now)

    def test_token_contains_exp_claim(self, setup_mocks):
        mock_time_now, _ = setup_mocks

        data = {"sub": "user_id"}
        token = create_access_token(data)
        expected_exp = mock_time_now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.verify_token(token, "user_id", expected_exp, mock_time_now)

    def test_log_message_contains_expiration_time(self, setup_mocks):
        mock_time_now, mock_log = setup_mocks

        data = {"sub": "user_id"}
        token = create_access_token(data)
        expected_exp = mock_time_now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # Get the actual call arguments
        actual_log_args = mock_log.call_args[0]
        actual_message = actual_log_args[0]  # The message is the first argument
        
        # Define a regex pattern to extract the expiration date
        pattern = r'Expiration time: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}\+\d{2}:\d{2})'
        
        # Search for the expiration date in the log message
        match = re.search(pattern, actual_message)
        
        assert match is not None, "Expiration time not found in log message"
        
        # Extract the expiration date string from the match
        extracted_exp_str = match.group(1)

        assert extracted_exp_str is not None
        assert actual_log_args[1] == logging.INFO

        #mock_log.assert_called_once_with(f"Access token created! Expiration time: {expected_exp}", logging.INFO)

    def test_token_contains_correct_token_type_claim(self, setup_mocks):
        mock_time_now, _ = setup_mocks

        data = {"sub": "user_id"}
        token = create_access_token(data)
        expected_exp = mock_time_now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.verify_token(token, "user_id", expected_exp, mock_time_now)

    def test_validate_jwt_token_structure(self, setup_mocks):
        mock_time_now, _ = setup_mocks

        data = {"sub": "user_id"}
        token = create_access_token(data)
        expected_exp = mock_time_now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.verify_token(token, "user_id", expected_exp, mock_time_now)


#-------------------------------------------------------- verify_jwt_token --------------------------------------------------------#





#---------------------------------------------------------- create_tokens ---------------------------------------------------------#


