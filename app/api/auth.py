from fastapi import APIRouter, Depends, HTTPException
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

# Define your auth routes here
@auth_router.post("/login")
def login():
    # Login logic here
    pass

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

@auth_router.post("/register")
def register():
    # Registration logic here
    pass