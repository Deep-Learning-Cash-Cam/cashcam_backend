import logging
import secrets
from sqlalchemy.orm import Session
from ultralytics import settings
from app.db import db_models
from app.schemas import image_schemas, user_schemas
from app.core.security import get_password_hash, verify_password
from app.logs import log

# ----------------------------------------------------------- User api ----------------------------------------------------------- #

def get_user(db: Session, user_id: int) -> db_models.User | None:
    user = db.query(db_models.User).filter(db_models.User.id == user_id).first()
    if user:
        return user

def get_user_by_email(db: Session, email: str) -> db_models.User | None:
    user = db.query(db_models.User).filter(db_models.User.email == email).first()
    if user:
        return user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(db_models.User).offset(skip).limit(limit).all()

# Create a local user
def create_user(db: Session, user: user_schemas.UserCreateRequest) -> db_models.User | None:
    
    # Check all fields are filled
    if not user.password or not user.email or not user.name:
        log("User creation failed - missing fields", logging.WARNING)
        return None
    
    # Hash the password and create a new user object
    hashed_password = get_password_hash(user.password)
    db_user = db_models.User(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name
        )
    
    if not db_user:
        log("User creation failed", logging.ERROR)
        return None
    
    # Add the user to the database and return the user
    db.add(db_user)
    db.commit()
    db.refresh(db_user) # Refresh the db_user object to get the new id
    
    log(f"User created successfully! id:{db_user.id}")
    return db_user

# Authenticate a user upon local login (email and password)
def authenticate_user(db: Session, email: str, password: str) -> db_models.User | None:
    # Query the database for a user with the given email
    user = db.query(db_models.User).filter(db_models.User.email == email).first()
    
    # Check if a user was found and if so, verify the password
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user

# Update user information
def update_user(db: Session, user_id: int, user_update: user_schemas.UserUpdate) -> db_models.User | None:
    # Find the user in the database
    db_user = db.query(db_models.User).filter(db_models.User.id == user_id).first()
    
    # If the user is found, update the user's information
    if db_user:
        update_data = user_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_user, key, value) # Set the new value for the key
        db.commit()
        db.refresh(db_user) # Refresh the db_user object to get the new values before returning it
    else:
        log(f"User with id:{user_id} not found", logging.WARNING)
        
    return db_user

# Update user password
def update_user_password(db: Session, user_id: int, user_update: user_schemas.UserUpdatePassword) -> db_models.User | None:
    # Find the user in the database
    db_user = db.query(db_models.User).filter(db_models.User.id == user_id).first()
    
    # If the user is found, update the user's password
    if db_user:
        hashed_password = get_password_hash(user_update.password)
        db_user.hashed_password = hashed_password
        db.commit()
        log(f"Password updated for user id:{user_id}", debug=True)
    else:
        log(f"User with id:{user_id} not found", logging.WARNING)
    return db_user

# Delete a user from the database by id
def delete_user(db: Session, user_id: int) -> bool:
    # Find the user in the database
    db_user = db.query(db_models.User).filter(db_models.User.id == user_id).first()
    
    if db_user: # If the user is found, delete the user
        db.delete(db_user)
        db.commit()
        log(f"User deleted, id:{user_id}")
        return True
    return False

# Based on the Google ID, get or create a user
def get_or_create_user_by_google_id(db: Session, google_id: str, email: str, name: str) -> db_models.User:
    # Check if a user with the same Google ID already exists
    db_user = db.query(db_models.User).filter(db_models.User.google_id == google_id).first()
    
    if not db_user: # If no user is found, create a new user
        db_user = db_models.User(google_id=google_id, email=email, name=name, hashed_password=None)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        log(f"New user created with Google ID:{google_id}, User ID: {db_user.id}")
    return db_user

# ----------------------------------------------------------- Image api ----------------------------------------------------------- #

# Get an image by the image id
def get_image(db: Session, image_id: int) -> db_models.Image | None:
    image = db.query(db_models.Image).filter(db_models.Image.id == image_id).first()
    if image:
        return image
    

# Add an image to the database and link it to a user by user id
def save_image(db: Session, image: str, user_id: int) -> db_models.Image:
    log(f"Adding image to the database for user id:{user_id}", debug=True)
    db_image = db_models.Image(base64_string= image, user_id=user_id, flagged=False, upload_date=settings.TIME_NOW)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    log(f"Image added successfully! id:{db_image.id}")

# Get all images from a user by user id
def get_images_by_user_id(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[db_models.Image] | None:
    images = db.query(db_models.Image).filter(db_models.Image.user_id == user_id).offset(skip).limit(limit).all()
    if images:
        return images

# Get all flagged images
def get_flagged_images(db: Session, skip: int = 0, limit: int = 100) -> list[db_models.Image] | None:
    flagged_images = db.query(db_models.Image).filter(db_models.Image.flagged == True).offset(skip).limit(limit).all()
    if flagged_images:
        return flagged_images

# Get all flagged images from a user by user id
def get_flagged_images_by_user_id(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[db_models.Image] | None:
    flagged_images = db.query(db_models.Image).filter(db_models.Image.user_id == user_id, db_models.Image.flagged == True).offset(skip).limit(limit).all()
    if flagged_images:
        return flagged_images
