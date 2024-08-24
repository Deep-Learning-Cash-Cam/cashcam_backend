import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file and add the project root to the Python path
load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Now we can import the FastAPI app and run it
from fastapi import Depends, FastAPI, HTTPException, Request
from app.core.config import settings
from app.api.endpoints.routes import router as api_router
from app.api.endpoints.auth import auth_router
from app.logs.logger_config import log
import asyncio
from app.db.database import engine, get_db
from app.db import crud, db_models
from app.services.currency_exchange import exchange_service
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from requests import Session

from app.api.dependencies import get_current_user_by_token
from app.core import security
from app.schemas import token_schemas, user_schemas

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up the server...")
    log("Server started.")

    # asyncio.create_task(exchange_service.update_rates_daily())
    db_models.Base.metadata.create_all(bind=engine)
    #TODO: Fix auth.py, db_api.py to allow for authentication
    
    #TODO: protect routes with authentication
    #TODO: add google authentication and local authentication
    #TODO: integrate db with the app
    #TODO: add tests
    yield # App running
    
    print("Shutting down the server...")
    log("Server shut down.")
    # close any open connections
    # save any data that might be lost
    # shutdown the model

app = FastAPI(lifespan=lifespan, title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET_KEY)
app.include_router(api_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix="/auth")

db_dependancy = Annotated[Session, Depends(get_db)]
user_dependancy = Annotated[user_schemas.User, Depends(get_current_user_by_token)]

@app.get("/")
async def root(request: Request):
    user = request.session.get("user")
    if user:
        return {"message": f"Welcome, {user['name']}!"}
    return {"message": "Welcome to CashCam!"}

#Allows to skip this function: 'uvicorn app.main:app --reload' and just run the main.py file
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.LOCAL_IP, port=settings.PORT, reload=True)
