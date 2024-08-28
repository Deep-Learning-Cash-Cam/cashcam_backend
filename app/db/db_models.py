from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import uuid
from app.core.config import settings

def generate_id(length=16):
    return str(uuid.uuid4().int)[:length]

# All the models here are used to interact with the database

# User as a db model
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default= generate_id()) # The ID is the primary key, unique and indexed
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    role = Column(String, default="user")
    name = Column(String)
    google_id = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=settings.TIME_NOW)
    
    images = relationship("Image", back_populates="user")
    
# Image as a db model
class Image(Base):
    __tablename__ = "images"

    id = Column(String, primary_key=True, index=True, default= generate_id())
    base64_string = Column(String)
    upload_date = Column(DateTime(timezone=True), default=settings.TIME_NOW)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # An image belongs to a user unless it was sent by an unregistered user (null)
    flagged = Column(Boolean, default=False) # When true, the image is flagged for review due to a possible error with prediction results

    user = relationship("User", back_populates="images")
    