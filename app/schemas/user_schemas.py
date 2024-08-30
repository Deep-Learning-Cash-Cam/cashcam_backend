from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator

# ----- These classes are used to define the structure of the data that will be sent to the backend by the app ----- #
password_description = "Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter and one digit."
password_min = 8
password_max = 25

def password_validator(password: str) -> str:
    # Check if the password meets the complexity requirements
    if len(password) < password_min:
        raise ValueError(f'Password must be at least {password_min} characters long.')
    if len(password) > password_max:
        raise ValueError(f'Password must be at most {password_max} characters long.')
    if not any(char.isdigit() for char in password):
        raise ValueError('Password must contain at least one digit.')
    if not any(char.islower() for char in password):
        raise ValueError('Password must contain at least one lowercase letter.')
    if not any(char.isupper() for char in password):
        raise ValueError('Password must contain at least one uppercase letter.')
    
    return password

# The base class for the user model, all classes that inherit from this class will have the following fields
class UserBase(BaseModel):
    email: EmailStr

# The class for creating a new user, with a password field added to the base class
class UserCreateRequest(UserBase):
    name: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length= password_min, max_length= password_max,
        description= password_description)
    
    @validator("password")
    def password_complexity(cls, password: str) -> str:
        return password_validator(password)

# How a user will be returned from the API
class User(UserBase):
    name: str
    id: str
    role: str
    google_id: Optional[str] = None
    # Exclude the hashed_password field from the response!

    class Config: # Set orm_mode to True to allow the class to be used in the ORM (The database)
        from_attributes = True
        
# Used to update a user's information
class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr] = None
    
# Used to update a user's password
class UserUpdatePassword(BaseModel):
    password: str = Field(..., min_length= password_min, max_length= password_max,
        description= password_description)
    
    @validator("password")
    def password_complexity(cls, password: str) -> str:
        return password_validator(password)
    
class UserLogin(UserBase):
    password: str
