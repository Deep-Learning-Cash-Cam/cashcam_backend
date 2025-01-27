from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.core import security
from app.schemas import user_schemas as user_schemas
from app.schemas import token_schemas as token_schemas
from app.db import crud
import requests
from app.core.config import settings
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
import logging
from typing import Annotated
from passlib.context import CryptContext
from app.logs.logger_config import log

auth_router = APIRouter()

SECRET_KEY = settings.JWT_ACCESS_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__min_rounds=12)
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[user_schemas.User | None, Depends(get_current_user)]

# ----------------------------------------------------------- Routes ----------------------------------------------------------- #

# Register a new user locally using name, email and password
@auth_router.post("/register", response_model=token_schemas.Token)
def register(form_data: user_schemas.UserCreateRequest, user: user_dependency, db: db_dependency):
    success_message = "User registered successfully"
    # Check if the user is already authenticated
    if user:
        log(f"User already authenticated", logging.INFO, debug=True)
        return security.create_tokens(token_schemas.TokenData(user_id=user.id, email=user.email))
    
    # Check if a user with the same email already exists
    db_user = crud.get_user_by_email(db, email=form_data.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # If the user does not exist, create a new user
    new_user = crud.create_user(db=db, user=form_data)
    if not new_user:
        log(f"User creation failed: {form_data}", logging.ERROR)
        raise HTTPException(status_code=400)
    
    # Return a success message and let the user know they can login under /auth/login
    return JSONResponse(content={"detail": success_message}, status_code=200)


# Local login route (email and password)
@auth_router.post("/login", response_model= token_schemas.Token)
async def login(form_data: user_schemas.UserLogin, user: user_dependency, db: db_dependency):
    # Set the credentials exception
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},)
    
    try:
        if user: # User is already authenticated, return the tokens
            log(f"User already authenticated", logging.INFO, debug=True)
            return security.create_tokens(token_schemas.TokenData(user_id=user.id, email=user.email))
    except Exception as e:
        # User is not authenticated, continue
        log(f"User not found - {str(e)}", logging.INFO)
    
    # No user is found. Check if the email and password are correct
    found_user = crud.authenticate_user(db, email=form_data.email, password=form_data.password)
    log(f"here2: {found_user}")
    if not found_user: # User not found
        raise credentials_exception
    
    return security.create_tokens(token_schemas.TokenData(user_id=found_user.id, email=found_user.email))


# LOGOUT SHOULD BE DONE IN THE FRONTEND BY DELETEING THE TOKENS
# Logout user by deleting the refresh token and access token
@auth_router.post("/logout")
def logout(request: Request, response: Response):
    # Set the user to None
    request.state.user = None
    
    # Delete the access token and refresh token from the cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    return {"detail": "Successfully logged out"}

# Return the current user's information
@auth_router.get("/users/me", response_model=user_schemas.User, status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user_schemas.User(id=user.id, email=user.email, name=user.name, role=user.role, google_id=user.google_id)


# Used to create tokens with password and email
@auth_router.post("/token", response_model=token_schemas.Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    # ----------- OAuth2PasswordRequestForm requires a username field, the email is used as the username ----------- #
    user = crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user: # User not found
        raise HTTPException(status_code=400, detail="Unauthorized")
    
    # Create access and refresh tokens and return them
    return security.create_tokens(token_schemas.TokenData(user_id=user.id, email=user.email))


#TODO: TEST ROUTE
@auth_router.post("/refresh_token", response_model=token_schemas.Token)
async def refresh_token(refresh_token: str, user: user_dependency):
    invalid_token_exception = HTTPException(status_code=401, detail="Invalid token")

    if user: # User is already authenticated, return the tokens
        log(f"User already authenticated", logging.INFO, debug=True)
        return security.create_tokens(token_schemas.TokenData(user_id=user.id, email=user.email))
    
    # Else, try to authenticate the refresh token
    payload = security.verify_jwt_token(token= refresh_token, is_refresh=True)
    if payload: # Token is valid, return new tokens
        user_id = payload.get("sub")
        user_email = payload.get("email")
        if user_id is None or user_email is None:
            log(f"User ID or email not found in token", logging.ERROR, debug=True)
            raise invalid_token_exception
        
        log(f"Tokens refreshed for user: {user_id}", logging.INFO, debug=True)
        return security.create_tokens(token_schemas.TokenData(user_id= user_id, email= user_email))
    else: # Token is invalid
        raise invalid_token_exception

# ----------------------------------------------------------- Google auth ----------------------------------------------------------- #

from google.oauth2 import id_token
from google.auth.transport import requests
from google.auth.exceptions import GoogleAuthError

CLIENT_IDS = [settings.GOOGLE_CLIENT_IOS_ID, settings.GOOGLE_CLIENT_ANDROID_ID]

@auth_router.post("/google-signin")
async def google_signin(token_data: token_schemas.GoogleToken, db: db_dependency):
    error_message = "Invalid token"
    token_exception = HTTPException(
        status_code=401,
        detail={"error": f"Failed to authenticate with Google-Auth: {error_message}",
                "identifier": "google_auth_error"})
    
    try:
        for GOOGLE_CLIENT_ID in CLIENT_IDS: # Try each client ID
            try:
                # Verify the token using Google's verification method
                id_info = id_token.verify_oauth2_token(token_data.token_id, requests.Request(), GOOGLE_CLIENT_ID)

                # User ID doesn't match the user ID in the token
                if id_info['aud'] != GOOGLE_CLIENT_ID:
                    log(f"Invalid client ID: {id_info['aud']}", logging.WARNING, debug=True)
                    error_message = "Invalid client ID"
                    continue

                # Optionally, check if the token is issued by Google accounts
                if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                    log(f"Invalid issuer: {id_info['iss']}", logging.WARNING, debug=True)
                    error_message = "Invalid issuer"
                    continue

                # User is authenticated, and you can retrieve user information
                user_id = id_info['sub']
                email = id_info.get('email')
                name = id_info.get('name')
                if not email or not name or not user_id:
                    log(f"Email / name / user_id not found in token: {id_info}", logging.ERROR, debug=True)
                    error_message = "Email / name / user_id not found in token"
                    continue

                # Register the user if they don't exist in the database
                new_user = crud.get_or_create_user_by_google_id(db, google_id=user_id, email=email, name=name)
                if not new_user:
                    log(f"User creation failed: {email}", logging.CRITICAL)
                    # Can't allow this to fail, raise an exception
                    error_message = "User creation error"
                    raise token_exception
                
                # User authenticated, return the tokens
                return security.create_tokens(token_schemas.TokenData(user_id=new_user.id, email=new_user.email))

            except ValueError as e:
                # Invalid token, try the next client ID
                continue
            
            except GoogleAuthError as e:
                # Issuer invalid error
                log(f"GoogleAuthError: {str(e)}", logging.ERROR, debug=True)
                error_message = "Google authentication failed"
                continue
            
        # All client IDs failed
        log(f"Invalid token: {token_data.token_id}", logging.WARNING, debug=True)
        raise token_exception
    
    except Exception as e:
        if isinstance(e.detail, dict) and e.detail.get("identifier") == "google_auth_error":
        # token_exception was raised, re-raise it
            raise e
        
        # General error
        log(f"Error in google_signin: {str(e)}", logging.ERROR)
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
