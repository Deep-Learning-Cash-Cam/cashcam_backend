from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from .database import Base
import secrets
from app.core.config import settings

# All the models here are used to interact with the database

# Generate an ID for the user
def generate_id() -> BigInteger:
    return BigInteger(str(secrets.token_urlsafe(63)))

# User as a db model
class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, default=generate_id) # The ID is the primary key, unique and indexed
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    role = Column(String, default="user")
    name = Column(String)
    google_id = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=settings.TIME_NOW)
    
    images = relationship("Image", back_populates="user")
    
# Image as a db model
class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    filepath = Column(String)
    upload_date = Column(DateTime, default=settings.TIME_NOW)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True) # An image belongs to a user unless it was sent by an unregistered user (null)
    flagged = Column(bool, default=False) # When true, the image is flagged for review due to a possible error with prediction results

    user = relationship("User", back_populates="images")
    