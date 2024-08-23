from typing import Optional
from pydantic import BaseModel, EmailStr, Field

# ----- These classes are used to define the structure of the data that will be sent to the backend by the app ----- #
password_regex = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[a-zA-Z]).{8,}$'
password_description = "Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter and one digit."
password_min = 8
password_max = 25

# The base class for the user model, all classes that inherit from this class will have the following fields
class UserBase(BaseModel):
    email: EmailStr

# The class for creating a new user, with a password field added to the base class
class UserCreate(UserBase):
    name: str = Field(..., min_length=2, max_length=50)
    password: str = Field(min_length= password_min, max_length= password_max,
        regex= password_regex,
        description= password_description)
    
# Used for logging in, with a password field added to the base class
class UserLogin(UserBase):
    password: str

# How a user will be returned from the API
class User(UserBase):
    id: int
    role: str
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
        regex= password_regex,
        description= password_description)
