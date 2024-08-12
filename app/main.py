import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file and add the project root to the Python path
load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Now we can import the FastAPI app and run it
from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import router as api_router
from app.logs.logger_config import log
import asyncio
from app.services.currency_exchange import exchange_service
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up the server...")
    log("Server started.")

    asyncio.create_task(exchange_service.update_rates_daily())
    #TODO: connect to the database
    yield # App running
    
    print("Shutting down the server...")
    log("Server shut down.")
    # close any open connections
    # save any data that might be lost
    # shutdown the model

app = FastAPI(lifespan=lifespan, title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/")
async def root():
    return {"message": "Welcome to CashCam!"}

#Allows to skip this function: uvicorn app.main:app --reload and just run the main.py file
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.LOCAL_IP, port=settings.PORT, reload=True)
