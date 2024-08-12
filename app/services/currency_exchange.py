import logging
import httpx
import asyncio
import json
import os
from datetime import datetime, timedelta
from app.core.config import settings
from app.logs.logger_config import log
API_KEY = settings.EXCHANGE_RATE_API_KEY

class ExchangeRateService:
    BASE_URL = "https://v6.exchangerate-api.com/v6"
    CURRENCIES = ["EUR", "USD", "ILS"]
    CACHE_FILE = "app/logs/exchange_rates_cache.json"
    
    def __init__(self):
        self.rates = {}
        self.last_update = None

    async def fetch_rates(self):
        async with httpx.AsyncClient() as client:
            for base in self.CURRENCIES:
                url = f"{self.BASE_URL}/{API_KEY}/latest/{base}"
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data["result"] == "success":
                        for target in self.CURRENCIES:
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
            self.save_rates_to_file()
            log(f"Exchange rates updated successfully: {self.rates}")
        else:
            log("Failed to fetch any exchange rates", logging.CRITICAL)
        
    def save_rates_to_file(self):
        data = {
            "rates": self.rates,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }
        with open(self.CACHE_FILE, "w") as f:
            json.dump(data, f)
            
    def load_rates_from_file(self):
        if os.path.exists(self.CACHE_FILE):
            with open(self.CACHE_FILE, 'r') as file:
                data = json.load(file)
            self.rates = data["rates"]
            self.last_update = datetime.fromisoformat(data["last_update"]) if data["last_update"] else None
            return True
        return False

    async def update_rates_daily(self):
        # Only fetch if rates are not available or last update was more than a day ago, try to load from file first
        if not self.rates or self.last_update is None or datetime.now() - self.last_update > timedelta(days=1):
            log("Starting daily exchange rate update")
            await self.fetch_rates()
            await asyncio.sleep(24 * 60 * 60)  # Sleep for 24 hours
            
    def get_exchange_rates(self):
        if self.should_update_rates():
            if not self.load_rates_from_file() or self.should_update_rates():
                log("Rates need updating, but can't fetch asynchronously. Using old rates.")
            else:
                log("Loaded rates from file")
        else:
            log("Using existing rates - No fetch needed")
        return self.rates

    async def get_exchange_rates_async(self):
        if self.should_update_rates():
            if not self.load_rates_from_file() or self.should_update_rates():
                log("Fetching new exchange rates from API")
                await self.fetch_rates()
            else:
                log("Loaded rates from file")
        else:
            log("Using existing rates - No fetch needed")
        return self.rates
    
    def should_update_rates(self):
        return not self.rates or self.last_update is None or datetime.now() - self.last_update > timedelta(days=1)
        
exchange_service = ExchangeRateService()