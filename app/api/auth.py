from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core import security
from app.schemas import user as user_schemas
from app.schemas import token as token_schemas
from app.db import db_api
from app.core.config import settings
from app.db.database import get_db
from sqlalchemy.orm import Session
from datetime import timedelta

auth_router = APIRouter()

# PLACEHOLDER

# Local login route (email and password)
from fastapi import APIRouter, Depends, HTTPException, status
from app.core import security
from app.schemas import user as user_schemas
from app.schemas import token as token_schemas
from app.db import db_api
from app.core.config import settings
from app.db.database import get_db
from sqlalchemy.orm import Session
from datetime import timedelta

auth_router = APIRouter()

# Handle the login route (email and password)
@auth_router.post("/login", response_model=token_schemas.Token)
def login(
    login_data: user_schemas.UserLogin, # Contains the email and password
    db: Session = Depends(get_db) # Get the database session
):
    # Authenticate the user
    user = db_api.authenticate_user(db, email=login_data.email, password=login_data.password)
    
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
@auth_router.post("/login/access-token", response_model=token_schemas.Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = db_api.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

# Register a new user locally using name, email and password
@auth_router.post("/register", response_model=user_schemas.User)
def register(
    user: user_schemas.UserCreate, 
    db: Session = Depends(get_db)
):
    # Check if a user with the same email already exists
    db_user = db_api.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    # If the user does not exist, create a new user and return it
    return db_api.create_user(db=db, user=user)