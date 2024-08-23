from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core import security
from app.schemas import user_schemas as user_schemas
from app.schemas import token_schemas as token_schemas
from app.db import crud
from app.core.config import settings
from app.db.database import get_db
from sqlalchemy.orm import Session
from datetime import timedelta

auth_router = APIRouter()

# ----------------------------------------------------------- Routes ----------------------------------------------------------- #

# Local login route (email and password)
@auth_router.post("/login", response_model=token_schemas.Token)
def login(
    login_data: user_schemas.UserLogin, # Contains the email and password
    db: Session = Depends(get_db) # Get the database session
):
    # first, check if the user is already authenticated
    token = login_data.headers.get("Authorization")
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
    user = crud.authenticate_user(db, email=login_data.email, password=login_data.password)
    
    # If authentication fails, raise an exception
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # If authentication succeeds, create an access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email},  # link the token to the user's email
        expires_delta=access_token_expires
    )
    
    # Return the token
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# Handle the login access token route (for OAuth2) for the returned token
@auth_router.post("/google/login", response_model=token_schemas.Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
    
#TODO: FINISH THIS ROUTE
@auth_router.get("/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    # Get the user's information from Google using the code
    user_info = security.get_google_user_info(code)
    
    # Check if the user is already registered
    db_user = crud.get_user_by_email(db, email=user_info.email)
    if db_user:
        # If the user is already registered, return the user's information
        return db_user
    
    # If the user is not registered, create a new user
    new_user = crud.create_user(db=db, user=user_info)
    return new_user


# Register a new user locally using name, email and password
@auth_router.post("/register", response_model=token_schemas.Token)
def register(user: user_schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if a user with the same email already exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # If the user does not exist, create a new user
    new_user = crud.create_user(db=db, user=user)
    
    # Create tokens for the new user with the user's id and email
    access_token_data = {"sub": str(new_user.id), "email": new_user.email}
    access_token = security.create_access_token(data=access_token_data)
    refresh_token = security.create_refresh_token(data=access_token_data)

    # Return the tokens with token type "bearer" for OAuth2
    return { "access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


# Logout user by deleting the refresh token and access token
@auth_router.post("/logout")
def logout(response: Response):
    # Delete the access token and refresh token from the cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"detail": "Successfully logged out"}