from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from .database import Base
import secrets
from app.core.config import settings

# Generate an ID for the user
def generate_id() -> BigInteger:
    return BigInteger(str(secrets.token_urlsafe(63)))

# User as a db model
class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, default=generate_id, index=True) # The ID is the primary key, unique and indexed
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")
    
    images = relationship("Image", back_populates="user")
    
# Image as a db model
class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    filepath = Column(String)
    upload_date = Column(DateTime, default=settings.TIME_NOW)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="images")