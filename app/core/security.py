from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.core.config import settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create an access token for JWT (JSON Web Token)
def create_access_token(data: dict, expires_delta: timedelta = None):
    # Copy the data
    to_encode = data.copy()
    
    # Check if expires_delta is set and update if needed
    if expires_delta: # If expires_delta is set, update the expiration time
        expire = settings.TIME_NOW + expires_delta
    else: # If expires_delta is not set, use the default expiration time
        expire = settings.TIME_NOW + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Update the expiration time in the data
    to_encode.update({"exp": expire})
    
    # Encode the data and return the token
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_password(plain_password, hashed_password):
    return password_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_context.hash(password)