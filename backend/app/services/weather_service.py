"""
Weather Integration Service for KrishiMitra AI.
Integrates live weather forecasting (Open-Meteo & OpenWeatherMap) with agricultural interpretations.
"""

import os
import time
import logging
import httpx
import pandas as pd
from typing import Dict, Any, Optional
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "processed")

# WMO Weather interpretation codes
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm"
}


class WeatherService:
    def __init__(self):
        self.geo_df = None
        self.weather_normals_df = None
        self._weather_cache: Dict[str, tuple] = {}
        self._cache_ttl_seconds: float = 300.0  # 5-minute TTL
        self._load_geo()

    def _load_geo(self):
        geo_path = os.path.join(DATA_DIR, "clean_geography.csv")
        weather_path = os.path.join(DATA_DIR, "clean_weather.csv")
        if os.path.exists(geo_path):
            self.geo_df = pd.read_csv(geo_path)
        if os.path.exists(weather_path):
            self.weather_normals_df = pd.read_csv(weather_path)

    def get_coordinates(self, state: str, district: str) -> Optional[tuple]:
        """Looks up latitude and longitude for a given state and district."""
        if self.geo_df is None:
            return None
        match = self.geo_df[
            (self.geo_df["State_Name"].str.lower() == state.lower().strip()) &
            (self.geo_df["District_Name"].str.lower() == district.lower().strip())
        ]
        if not match.empty:
            return float(match.iloc[0]["latitude"]), float(match.iloc[0]["longitude"])
        return None

    def _generate_agro_interpretation(self, temp: float, humidity: float, rainfall: float, wind: float) -> str:
        """Generates evidence-backed agricultural advisory based on live weather data."""
        advisories = []

        # Rainfall / Irrigation
        if rainfall == 0.0:
            advisories.append("No immediate precipitation recorded. Ensure scheduled irrigation is maintained for moisture-sensitive crops.")
        elif rainfall > 30.0:
            advisories.append("Heavy rainfall observed/expected. Ensure field drainage channels are clear to prevent waterlogging around roots.")
        else:
            advisories.append(f"Light to moderate rainfall ({rainfall:.1f} mm) received; postpone light irrigation to conserve water.")

        # Wind & Spraying
        if wind > 5.0:
            advisories.append(f"Wind speed is elevated ({wind:.1f} m/s). Avoid spraying foliar fertilizers or pesticides to minimize chemical drift.")
        else:
            advisories.append("Wind conditions are calm and favorable for scheduled pesticide or nutrient foliar spraying.")

        # Temperature / Humidity Disease pressure
        if humidity > 75 and 22 <= temp <= 32:
            advisories.append("High humidity combined with warm temperatures creates favorable conditions for fungal foliar diseases (e.g. blast, blight). Monitor leaves closely.")
        elif temp > 38:
            advisories.append("High ambient temperature alert. Provide light evening irrigation or mulching to mitigate heat stress.")

        return " ".join(advisories)

    async def get_weather(
        self,
        state: Optional[str] = None,
        district: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Retrieves real-time weather and 7-day forecast with agricultural interpretation.
        """
        # Resolve coordinates
        if (lat is None or lon is None) and state and district:
            coords = self.get_coordinates(state, district)
            if coords:
                lat, lon = coords
            else:
                lat, lon = 17.3850, 78.4867  # Default central India (Hyderabad) coordinates

        if lat is None or lon is None:
            lat, lon = 20.5937, 78.9629

        cache_key = f"{(state or '').lower().strip()}__{(district or '').lower().strip()}__{round(lat, 4)}__{round(lon, 4)}"
        now = time.time()
        if cache_key in self._weather_cache:
            ts, cached_res = self._weather_cache[cache_key]
            if now - ts < self._cache_ttl_seconds:
                return cached_res

        # Fetch from Open-Meteo
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m"
                f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum"
                f"&timezone=Asia%2FKolkata"
            )

            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    curr = data.get("current", {})
                    daily = data.get("daily", {})

                    temp = float(curr.get("temperature_2m", 25.0))
                    rh = float(curr.get("relative_humidity_2m", 60.0))
                    precip = float(curr.get("precipitation", 0.0))
                    wind = float(curr.get("wind_speed_10m", 2.0))
                    code = curr.get("weather_code", 0)
                    condition = WMO_CODES.get(code, "Clear")

                    # Build 7-day forecast
                    forecast_list = []
                    dates = daily.get("time", [])
                    max_temps = daily.get("temperature_2m_max", [])
                    min_temps = daily.get("temperature_2m_min", [])
                    rains = daily.get("precipitation_sum", [])
                    codes = daily.get("weather_code", [])

                    for i in range(len(dates)):
                        forecast_list.append({
                            "date": dates[i],
                            "max_temp_c": max_temps[i] if i < len(max_temps) else None,
                            "min_temp_c": min_temps[i] if i < len(min_temps) else None,
                            "rainfall_mm": rains[i] if i < len(rains) else 0.0,
                            "condition": WMO_CODES.get(codes[i], "Clear") if i < len(codes) else "Clear"
                        })

                    advisory = self._generate_agro_interpretation(temp, rh, precip, wind)

                    res = {
                        "success": True,
                        "location": {
                            "state": state or "Detected Location",
                            "district": district or "Detected Region",
                            "latitude": round(lat, 4),
                            "longitude": round(lon, 4)
                        },
                        "current": {
                            "temperature_c": temp,
                            "relative_humidity_pct": rh,
                            "rainfall_mm": precip,
                            "wind_speed_ms": wind,
                            "condition": condition,
                            "weather_code": code
                        },
                        "forecast": forecast_list,
                        "agricultural_advisory": advisory,
                        "data_source": "Open-Meteo High-Resolution Live Meteorological Service"
                    }
                    self._weather_cache[cache_key] = (now, res)
                    return res
        except Exception as e:
            logger.warning(f"Live weather fetch failed: {e}. Falling back to historical district normals.")

        # Fallback to historical normals
        if self.weather_normals_df is not None and state and district:
            key = f"{state.lower().strip()}__{district.lower().strip()}"
            match = self.weather_normals_df[self.weather_normals_df["district_key"] == key]
            if not match.empty:
                row = match.iloc[0]
                return {
                    "success": True,
                    "location": {"state": state, "district": district, "latitude": lat, "longitude": lon},
                    "current": {
                        "temperature_c": round(float(row["mean_temperature_c"]), 1),
                        "relative_humidity_pct": round(float(row["relative_humidity_pct"]), 1),
                        "rainfall_mm": 0.0,
                        "wind_speed_ms": round(float(row["wind_speed_ms"]), 1),
                        "condition": "Historical Climate Normal"
                    },
                    "forecast": [],
                    "agricultural_advisory": "Live weather feed currently unavailable. Displaying multi-year historical climate normals from IMD dataset.",
                    "data_source": "IMD Historical Weather Dataset"
                }

        return {
            "success": False,
            "error": {
                "code": "WEATHER_UNAVAILABLE",
                "message": "Live weather is currently unavailable."
            }
        }


# Singleton instance
weather_service = WeatherService()
