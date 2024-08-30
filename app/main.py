import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file and add the project root to the Python path
load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Now we can import the FastAPI app and run it
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.endpoints.routes import router as api_router
from app.api.dependencies import get_current_user
from app.schemas import user_schemas
from app.api.endpoints.auth import auth_router
from app.logs.logger_config import log
import asyncio
from app.db.database import engine
from app.db import db_models
from app.services.currency_exchange import exchange_service
from contextlib import asynccontextmanager
from typing import Annotated, List

# Main function to run when the app starts
@asynccontextmanager
async def lifespan(app: FastAPI):
    server_tasks: List[asyncio.Task] = []
    try:
        log("Server started.")
        # Create the database tables
        db_models.Base.metadata.create_all(bind=engine)
        # Create exchange rate task
        fetch_exchange_rate_task = asyncio.create_task(exchange_service.update_rates_daily())
        server_tasks.append(fetch_exchange_rate_task)
        
        #TODO: protect routes with authentication

        yield # App running
    finally:
        # Close all tasks
        for task in server_tasks:
            task.cancel()
        await asyncio.gather(*server_tasks, return_exceptions=True)
        # Close the database engine
        engine.dispose()
        
        log("Server shut down.")

# Create the FastAPI app and routers

app = FastAPI(lifespan=lifespan, title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
app.include_router(api_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix="/auth")

# Global exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    detailed_errors = []

    for err in errors:
        detailed_error = {
            "field": err.get("loc")[-1],  # Get the field name
            "error": err.get("msg"),      # The validation error message
            "type": err.get("type")       # The type of error
        }
        detailed_errors.append(detailed_error)

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation Error",
            "errors": detailed_errors
        }
    )

# Root route
user_dependency = Annotated[user_schemas.User | None, Depends(get_current_user)]

@app.get("/")
async def root(request: Request, user: user_dependency):
    if user:
        return {"message": f"Welcome back, {user.name}!"}
    return {"message": "Welcome to CashCam!"}

#Allows to skip this function: 'uvicorn app.main:app --reload' and just run the main.py file
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.LOCAL_IP, port=settings.PORT, reload=True)
