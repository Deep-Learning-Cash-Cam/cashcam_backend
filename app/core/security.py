import logging
from typing import Optional, Tuple
from passlib.context import CryptContext
from datetime import timedelta
from jose import jwt, JWTError
from app.core.config import settings
from app.logs.logger_config import log

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__min_rounds=12)

# Create an access token for JWT (JSON Web Token) for the user
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    # Copy the data
    to_encode = data.copy()
    
    # Calculate the expiration time
    if expires_delta:
        new_expire_time = settings.TIME_NOW + expires_delta
    else:
        new_expire_time = settings.TIME_NOW + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Update the data
    to_encode.update({"exp": new_expire_time, "token_type": "access"})
    
    # Encode the data and return the token
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    log(f"Access token created! Expiration time: {new_expire_time}", logging.INFO)
    return encoded_jwt


# Create a refresh token for JWT (JSON Web Token)
def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    # Copy the data
    to_encode = data.copy()
    
    # Calculate the expiration time
    if expires_delta:
        new_expire_time = settings.TIME_NOW + expires_delta
    else:
        new_expire_time = settings.TIME_NOW + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Update the data
    to_encode.update({"exp": new_expire_time, "token_type": "refresh"})
    
    # Encode the data and return the token
    encoded_jwt = jwt.encode(to_encode, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    log(f"Refresh token created! Expiration time: {new_expire_time}", logging.INFO)
    return encoded_jwt


# Verify a JSON web token
def verify_token(token: str, token_type: str) -> Optional[dict]:
    try: #Check if the token is access or refresh
        if token_type == "access":
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        elif token_type == "refresh":
            payload = jwt.decode(token, settings.JWT_REFRESH_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        else: # Token type is invalid, raise an exception
            log(f"Invalid token type was sent. Got {token_type}", logging.WARNING)
            raise ValueError(f"Invalid token type! Got: {token_type}")
        
        # Check if the token type matches the expected token type
        if payload["token_type"] != token_type:
            log(f"Token type mismatch. Expected: {token_type}, Got: {payload['token_type']}", logging.WARNING)
            raise ValueError("Token type mismatch")
        
        # Check if the token is expired
        if "exp" not in payload:
            log(f"Token does not have an expiration time", logging.ERROR)
            raise ValueError("Token does not have an expiration time")
        
        if settings.TIME_NOW >= payload["exp"]:
            log(f"{token_type} token has expired", logging.INFO, debug=True)
            raise ValueError(f"{token_type.capitalize()} token has expired")
        
        # Return the payload if all checks pass
        return payload
    
    except (JWTError, ValueError) as e: # If an error occurs, log it and return None
        log(f"Error while verifying token: {str(e)}", logging.ERROR)
        return None
    
# Create both access and refresh tokens
def create_tokens(data: dict) -> Tuple[str, str]:
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    log("Access and refresh tokens created successfully", logging.INFO, debug=True)
    return access_token, refresh_token

# Verify a password against a hashed password
def verify_password(plain_password, hashed_password):
    return password_context.verify(plain_password, hashed_password)

# Hash a password
def get_password_hash(password):
    return password_context.hash(password)