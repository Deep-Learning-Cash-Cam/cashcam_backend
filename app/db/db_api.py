from sqlalchemy.orm import Session
from app.db import db_models
from app.schemas import user as user_schemas
from app.core.security import get_password_hash, verify_password
from app.logs import log

# ----------------------------------------------------------- User api ----------------------------------------------------------- #

def get_user(db: Session, user_id: int):
    return db.query(db_models.User).filter(db_models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(db_models.User).filter(db_models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(db_models.User).offset(skip).limit(limit).all()

# Create a local user
def create_user(db: Session, user: user_schemas.UserCreate):
    log("A new user is being created...", debug=True)
    
    # Hash the password and create a new user object
    hashed_password = get_password_hash(user.password)
    db_user = db_models.User(email=user.email, name=user.name ,hashed_password=hashed_password)
    
    # Add the user to the database and return the user
    db.add(db_user)
    db.commit()
    db.refresh(db_user) # Refresh the db_user object to get the new id
    
    log(f"User created successfully! id:{db_user.id}", debug=True)
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

# ----------------------------------------------------------- - ----------------------------------------------------------- #