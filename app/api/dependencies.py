import logging
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.db.db_models import User
from app.core.config import settings
from app.db.database import get_db
from app.core.security import verify_token
from app.logs.logger_config import log
from app.schemas.token_schemas import TokenData
from authlib.integrations.starlette_client import OAuth

# Extracts the token from the request's Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

db_dependancy = Annotated[Session, Depends(get_db)]

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    access_token_url="https://accounts.google.com/o/oauth2/token",
    access_token_params=None,
    refresh_token_url=None,
    refresh_token_params=None,
    redirect_uri="http://localhost:8000/auth/google/callback",
    client_kwargs={"scope": "openid profile email"},
)

# Get a user based on a token
async def get_current_user_by_token(token: Annotated[str, Depends(oauth2_scheme)], db: db_dependancy):
    # If the token is invalid, raise this exception
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},)
    
    # Try to decode the token
    try:
        payload = verify_jwt_token(token)
        if payload is None: # token is invalid
            log("Invalid token - verification failed", logging.INFO, debug=True)
            raise credentials_exception
        
        # Extract the email and user id from the payload
        user_id=payload.get("sub")
        user_email=payload.get("email")
        if user_id is None or user_email is None:
            log("Invalid token - missing id or email", logging.WARNING, debug=True)
            raise credentials_exception
        
    except (JWTError, ValidationError):
        log(f"Invalid token during {get_current_user_by_token.__name__}", logging.INFO, debug=True)
        raise credentials_exception
    
    # get the user based on the id
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None: # No user is found with the id
        log(f"User not found for {get_current_user_by_token.__name__}", logging.WARNING, debug=True)
        raise credentials_exception
    if user_email != user.email: # The email in the token does not match the user's email
        log(f"Email in token does not match the user's email for {get_current_user_by_token.__name__}", logging.ERROR)
        raise credentials_exception

    return user


def verify_jwt_token(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        log(f"Error while verifying token {token}", logging.INFO)
        log(str(e), logging.ERROR)
        return None
