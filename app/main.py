from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import router as api_router
from app.ml.model import model
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up the server...")
    # Startup
    model.load_model(settings.MODEL_PATH) # load the model
    #TODO: connect to external api for get exchange rates 
    # connect to the database if needed (Optional)
    
    yield # App running
    
    print("Shutting down the server...")
    # TODO: Shutdown logic
    # close any open connections
    # save any data that might be lost
    # shutdown the model

app = FastAPI(lifespan=lifespan, title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/")
async def root():
    return {"message": "Welcome to CashCam!"}


# post predict image value
# request: image (base64) + return currency
#
# response: 
# {
#     "currencies": {
#         "USD_C_50": {
#             "quantity": 2,
#             "return_currency_value": 1$
#         },
#         "EUR_B_1": {
#             "quantity": 5,
#             "return_currency_value": 6.7$
#         },
#         "NIS_C_100": {
#             "quantity": 1,
#             "return_currency_value": 3.6$
#         }
#     },
#     "image": "TODO" (Base64)
# }

# get exchange rate from external api during startup
# request: exchange rate of 1 USD to 1 EUR to 1 NIS

# USD:
# USD_C_1
# USD_C_5
# USD_C_10
# USD_C_25
# USD_C_50
# USD_C_100
#
# USD_B_1
# USD_B_2
# USD_B_5
# USD_B_10
# USD_B_20
# USD_B_50
# USD_B_100

# EUR:
# EUR_C_1
# EUR_C_2
# EUR_C_5
# EUR_C_10
# EUR_C_20
# EUR_C_50
# EUR_C_100
# EUR_C_200
#
# EUR_B_5
# EUR_B_10
# EUR_B_20
# EUR_B_50
# EUR_B_100
# EUR_B_200
# EUR_B_500

# NIS:
# NIS_C_10
# NIS_C_50
# NIS_C_100
# NIS_C_200
# NIS_C_500
# NIS_C_1000
#
# NIS_B_20
# NIS_B_50
# NIS_B_100
# NIS_B_200
