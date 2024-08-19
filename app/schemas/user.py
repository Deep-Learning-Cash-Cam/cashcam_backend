from pydantic import BaseModel, EmailStr

# The base class for the user model, all classes that inherit from this class will have the following fields
class UserBase(BaseModel):
    email: EmailStr

# The class for creating a new user, with a password field added to the base class
class UserCreate(UserBase):
    password: str

# How a user will be returned from the API
class User(UserBase):
    id: int
    role: str
    # Exclude the hashed_password field from the response!

    class Config: # Set orm_mode to True to allow the class to be used in the ORM (The database)
        from_attributes = True
