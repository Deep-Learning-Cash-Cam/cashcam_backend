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
    BASE_URL = "https://v6.exchangerate-api.com/v6" # API base URL
    CURRENCIES = ["EUR", "USD", "ILS"] # Currencies to fetch rates for
    CACHE_FILE = "app/services/exchange_rates_cache.json" # Path to store the exchange rates
    
    def __init__(self):
        self.rates = {}
        self.last_update = None

    # ----------------- Fetch exchange rates from the API, update the rates dictionary and store them in the cache file ----------------- #
    async def fetch_rates(self):
        log("Fetching exchange rates from API")
        async with httpx.AsyncClient() as client:
            for base in self.CURRENCIES:
                url = f"{self.BASE_URL}/{API_KEY}/latest/{base}"
                # Fetch from API
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    # If successful, update the rates dictionary
                    if data["result"] == "success":
                        for target in self.CURRENCIES:
                            if base != target:
                                self.rates[f"{base}_{target}"] = data["conversion_rates"][target]
                    
                    # Update cache file
                    self.save_rates_to_file()
                                
                    log(f"Successfully fetched rates for {base}")
                except httpx.HTTPStatusError as e:
                    log(f"HTTP error occurred while fetching rates for {base}: {str(e)}", logging.ERROR)
                except httpx.RequestError as e:
                    log(f"An error occurred while requesting rates for {base}: {str(e)}", logging.ERROR)
                except Exception as e:
                    log(f"An unexpected error occurred while fetching rates for {base}: {str(e)}", logging.ERROR)

        # ----------------- If rates were fetched successfully, update the last update time and save the rates to the cache file ----------------- #
        if self.rates:
            self.last_update = settings.TIME_NOW
            self.save_rates_to_file()
            log(f"Exchange rates updated successfully: {self.rates}")
        else:
            log("Failed to fetch any exchange rates", logging.CRITICAL)

    # ----------------- Save the exchange rates and last update time to the cache file ----------------- #
    def save_rates_to_file(self):
        data = {
            "rates": self.rates,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }
        with open(self.CACHE_FILE, "w") as f:
            json.dump(data, f)

    # ----------------- Load exchange rates and last update time from the cache file ----------------- #
    def load_rates_from_file(self):
        if os.path.exists(self.CACHE_FILE):
            with open(self.CACHE_FILE, 'r') as file:
                data = json.load(file)
            self.rates = data["rates"]
            self.last_update = datetime.fromisoformat(data["last_update"]) if data["last_update"] else None
            return True
        return False

    # ----------------- Update exchange rates daily based on last fetch time ----------------- #
    async def update_rates_daily(self):
        # Only fetch if rates are not available or last update was more UPDATE_RATES_INTERVAL_HOURS, try to load from file first
        while True:
            if not self.rates or self.last_update is None or settings.TIME_NOW - self.last_update > timedelta(hours=settings.UPDATE_RATES_INTERVAL_HOURS):
                log("Starting daily exchange rate update")
                await self.fetch_rates()

            await asyncio.sleep(settings.UPDATE_RATES_INTERVAL_HOURS * 60 * 60)  # Sleep for UPDATE_RATES_INTERVAL_HOURS hours

    # ----------------- Get exchange rates from the cache file or fetch them if needed ----------------- #
    # The endpoint function to use to get the exchange rates
    def get_exchange_rates(self):
        if self.should_update_rates():
            if not self.load_rates_from_file() or self.should_update_rates():
                log("Rates need updating, but can't fetch asynchronously. Using old rates.")
            else:
                log("Loaded rates from file")
        else:
            log("Using existing rates - No fetch needed")
        return self.rates

    # Should we update the rates based on last update time. Boolean function
    def should_update_rates(self):
        return not self.rates or self.last_update is None or settings.TIME_NOW - self.last_update > timedelta(days=1)

exchange_service = ExchangeRateService()