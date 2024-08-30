import json
from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, TypeDecorator
from sqlalchemy.orm import relationship
from .database import Base
from app.core.config import settings

# Custom JSON encoder for the currencies dictionary
class JSONEncodeDict(TypeDecorator):
    impl = String # The column type is a string

    # Convert the dictionary to a JSON
    def process_bind_param(self, dict_value, dialect):
        if dict_value is None:
            return '{}'
        return json.dumps(dict_value) #Convert the dictionary to a JSON

    # Convert the JSON to a dictionary
    def process_result_value(self, json_value, dialect):
        if json_value is None:
            return {}
        return json.loads(json_value) # Convert the JSON to a dictionary

# User as a db model
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default= settings.GET_ID) # The ID is the primary key, unique and indexed
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

    id = Column(String, primary_key=True, default= settings.GET_ID) # The ID is the primary key, unique and indexed
    base64_string = Column(String)
    upload_date = Column(DateTime(timezone=True), default=settings.TIME_NOW)
    user_id = Column(String, ForeignKey("users.id"), nullable=True) # An image belongs to a user unless it was sent by an unregistered user (null)
    currencies= Column(JSONEncodeDict) # The detected currencies and their respective amount in the image
    flagged = Column(Boolean, default=False) # When true, the image is flagged for review due to a possible error with prediction results

    user = relationship("User", back_populates="images")
