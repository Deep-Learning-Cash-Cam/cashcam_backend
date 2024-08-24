from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.api.dependencies import get_current_user_by_token
from app.core import security
from app.schemas import user_schemas as user_schemas
from app.schemas import token_schemas as token_schemas
from app.db import crud
import requests
from app.core.config import settings
from app.db.database import get_db
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import timedelta

from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth

import logging
from typing import Annotated, Optional, Tuple
from passlib.context import CryptContext
from app.logs.logger_config import log

auth_router = APIRouter()

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__min_rounds=12)
oauth2_beaer = OAuth2PasswordBearer(tokenUrl="auth/token")

db_dependancy = Annotated[Session, Depends(get_db)]
user_dependancy = Annotated[user_schemas.User, Depends(get_current_user_by_token)]

# ----------------------------------------------------------- Routes ----------------------------------------------------------- #

# Register a new user locally using name, email and password
@auth_router.post("/register", response_model=token_schemas.Token)
def register(user: user_schemas.UserCreateRequest, db: db_dependancy):
    # Check if a user with the same email already exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # If the user does not exist, create a new user
    new_user = crud.create_user(db=db, user=user)
    if not new_user:
        log(f"User creation failed: {user}", logging.ERROR)
        raise HTTPException(status_code=400)
    
    # return RedirectResponse(url="/auth/token")
    # Create tokens for the new user with the user's id and email
    access_token, refresh_token = security.create_tokens(data={"sub": new_user.id, "email": new_user.email},)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"}

# TODO: TEST THIS ROUTE
# Local login route (email and password)
@auth_router.post("/login", response_model= token_schemas.Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], # Contains the email and password
    db: db_dependancy
):
    # first, check if the user is already authenticated
    token = form_data.headers.get("Authorization")
    if token and token.startswith("Bearer "):
    # If the token is valid, return the token
    # If the token is invalid, the token will be ignored and the function will continue to authenticate the user
    # based on the email and password
        try:
            payload = security.verify_token(token)
            if payload:
                return {
                    "access_token": token,
                    "token_type": "bearer"
                }
        except Exception as e:
            # If the token is invalid, ignore it and continue to authenticate the user
            pass
    
    # Authenticate the user
    user = crud.authenticate_user(db, email=form_data.email, password=form_data.password)
    
    # If authentication fails, raise an exception
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # If authentication succeeds, create access and refresh tokens
    access_token, refresh_token = security.create_tokens(
        data={"sub": user.id, "email": user.email},  # link the token to the user's email
    )
    
    # Return the token
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
    
# TODO: TEST THIS ROUTE
# Logout user by deleting the refresh token and access token
@auth_router.post("/logout")
def logout(response: Response):
    # Delete the access token and refresh token from the cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"detail": "Successfully logged out"}

@auth_router.get("/users/me", response_model=user_schemas.User, status_code=status.HTTP_200_OK)
async def get_current_user(user: user_dependancy, db: db_dependancy):
    return user


# Used to create tokens with the user's id and email
@auth_router.post("/token", response_model=token_schemas.Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependancy):
    # ----------- OAuth2PasswordRequestForm requires a username field, the email is used as the username ----------- #
    user = crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user: # User not found
        raise HTTPException(status_code=400, detail="Unauthorized")
    
    # Create access and refresh tokens and return them
    access_token, refresh_token = security.create_tokens(data={"sub": user.id, "email": user.email},)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"}

#TODO: ADD REFRESH TOKEN ROUTE


# ----------------------------------------------------------- Google auth ----------------------------------------------------------- #
# TODO: TEST ALL GOOGLE AUTHENTICATION ROUTES
GOOGLE_CALLBACK_URI: str = "/google/callback"
GOOGLE_CLIENT_ID: str = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET: str = settings.GOOGLE_CLIENT_SECRET

@auth_router.get("/google/login")
async def google_login():
    return {
        "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_CALLBACK_URI}&scope=openid%20profile%20email&access_type=offline"
    }

@auth_router.get("/google/auth")
async def google_auth(code: str):
    token_url = "https://accounts.google.com/o/oauth2/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_CALLBACK_URI,
        "grant_type": "authorization_code"
    }
    response = requests.post(token_url, data= data)
    access_token = response.json().get("access_token")
    user_info = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", headers={"Authorization": f"Bearer {access_token}"})
    return user_info.json()

# @auth_router.get("/token")
# async def get_token(token: str = Depends(oauth2_scheme)):
#     return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


# # Handle the login access token route (for OAuth2) for the returned token
@auth_router.post("/google/login", response_model=token_schemas.Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token, refresh_token = security.create_tokens(
        data={"sub": user.id, "email": user.email},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"}
    
    
    
    
    
#TODO: FINISH THIS ROUTE
# @auth_router.get(GOOGLE_CALLBACK_URL)
# def google_callback(code: str, db: Session = Depends(get_db)):
#     # Get the user's information from Google using the code
#     user_info = security.get_google_user_info(code)
    
#     # Check if the user is already registered
#     db_user = crud.get_user_by_email(db, email=user_info.email)
#     if db_user:
#         # If the user is already registered, return the user's information
#         return db_user
    
#     # If the user is not registered, create a new user
#     new_user = crud.create_user(db=db, user=user_info)
#     return new_user




# TODO: ADD refresh token route



