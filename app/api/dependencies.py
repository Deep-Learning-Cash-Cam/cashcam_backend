import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.db.db_models import User
from app.core.config import settings
from app.db.database import get_db
from app.core.security import verify_token
from app.logs.logger_config import log
from app.schemas.token_schemas import TokenData

login_route = "/auth/login"

# Extracts the token from the request's Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=login_route)

# Get a user based on a token
async def get_current_user_by_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # If the token is invalid, raise this exception
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},)
    
    # Try to decode the token
    try:
        payload = verify_token(token)
        if payload is None: # token is invalid
            log("Invalid token - verification failed", logging.INFO, debug=True)
            raise credentials_exception
        
        # Extract the email and user id from the payload
        token_data = TokenData(id=payload.get("sub"), email=payload.get("email"))
    except (JWTError, ValidationError):
        log(f"Invalid token during {get_current_user_by_token.__name__}", logging.INFO, debug=True)
        raise credentials_exception
    # get the user based on the id
    user = db.query(User).filter(User.id == token_data.id).first()
    
    if user is None: # No user is found with the id
        log(f"User not found for {get_current_user_by_token.__name__}", logging.WARNING, debug=True)
        raise credentials_exception
    if token_data.email != user.email: # The email in the token does not match the user's email
        log(f"Email in token does not match the user's email for {get_current_user_by_token.__name__}", logging.WARNING, debug=True)
        raise credentials_exception

    return user








# Get a user based on a token
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # If the token is invalid, raise this exception
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},)
    
    # Try to decode the token
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    # Extract the email from the payload
    email = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    # If the token is valid, get the user based on the email
    user = db.query(User).filter(User.email == email).first()
    if user is None: # No user is found with the email
        raise credentials_exception
    
    # Return the user if it exists
    return user