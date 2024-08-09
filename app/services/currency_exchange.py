import httpx
import asyncio
from datetime import datetime, timedelta
from app.core.config import settings

#GET https://v6.exchangerate-api.com/v6/YOUR-API-KEY/latest/USD
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
                url = f"{BASE_URL}/{settings.EXCHANGE_RATE_API_KEY}/latest/{base}"
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                if data["result"] == "success":
                    for target in CURRENCIES:
                        if base != target:
                            self.rates[f"{base}_{target}"] = data["conversion_rates"][target]
        
        self.last_update = datetime.now()

    async def get_exchange_rates(self): # Update rates once a day at most
        if not self.rates or self.last_update is None or datetime.now() - self.last_update > timedelta(days=1):
            await self.fetch_rates()
        return self.rates

    async def update_rates_daily(self):
        while True:
            await self.fetch_rates()
            await asyncio.sleep(24 * 60 * 60)  # Sleep for 24 hours

exchange_service = ExchangeRateService()