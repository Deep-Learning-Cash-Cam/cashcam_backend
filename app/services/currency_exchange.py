# app/services/currency_exchange.py

import logging
import httpx
import asyncio
from datetime import datetime, timedelta
from app.core.config import settings
from app.logs import log

BASE_URL = "https://v6.exchangerate-api.com/v6"
CURRENCIES = ["EUR", "USD", "ILS"]
API_KEY = settings.EXCHANGE_RATE_API_KEY

class ExchangeRateService:
    def __init__(self):
        self.rates = {}
        self.last_update = None

    async def fetch_rates(self):
        async with httpx.AsyncClient() as client:
            for base in CURRENCIES:
                url = f"{BASE_URL}/{API_KEY}/latest/{base}"
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data["result"] == "success":
                        for target in CURRENCIES:
                            if base != target:
                                self.rates[f"{base}_{target}"] = data["conversion_rates"][target]
                                
                    log(f"Successfully fetched rates for {base}")
                except httpx.HTTPStatusError as e:
                    log(f"HTTP error occurred while fetching rates for {base}: {str(e)}", logging.ERROR)
                except httpx.RequestError as e:
                    log(f"An error occurred while requesting rates for {base}: {str(e)}", logging.ERROR)
                except Exception as e:
                    log(f"An unexpected error occurred while fetching rates for {base}: {str(e)}", logging.ERROR)
        
        if self.rates:
            self.last_update = datetime.now()
            log("Exchange rates updated successfully")
        else:
            log("Failed to fetch any exchange rates", logging.CRITICAL)

    async def get_exchange_rates(self):
        if not self.rates or self.last_update is None or datetime.now() - self.last_update > timedelta(days=1):
            log("Fetching new exchange rates")
            await self.fetch_rates()
        return self.rates

    async def update_rates_daily(self):
        while True:
            log("Starting daily exchange rate update")
            await self.fetch_rates()
            await asyncio.sleep(24 * 60 * 60)  # Sleep for 24 hours

exchange_service = ExchangeRateService()