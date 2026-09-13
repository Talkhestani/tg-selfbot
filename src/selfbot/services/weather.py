"""Weather service with provider abstraction and caching."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from time import time
from typing import ClassVar

import httpx

HTTP_TIMEOUT = 12.0
CACHE_TTL_SECONDS = 1800


class WeatherError(Exception):
    """Raised when weather data cannot be fetched."""


@dataclass(frozen=True)
class WeatherInfo:
    temperature: float
    feels_like: float | None
    description: str
    humidity: int | None
    wind_speed: float | None
    city: str
    country_code: str | None = None


class WeatherProvider(ABC):
    """Weather provider interface."""

    @abstractmethod
    async def get_weather(self, city: str) -> WeatherInfo:
        raise NotImplementedError


class OpenMeteoProvider(WeatherProvider):
    """Open-Meteo — free, no API key required."""

    _GEO_URL: ClassVar[str] = "https://geocoding-api.open-meteo.com/v1/search"
    _WEATHER_URL: ClassVar[str] = "https://api.open-meteo.com/v1/forecast"

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)

    async def get_weather(self, city: str) -> WeatherInfo:
        try:
            geo_response = await self._client.get(
                self._GEO_URL, params={"name": city, "count": 1, "language": "fa"}
            )
            geo_response.raise_for_status()
            geo = geo_response.json()
            results = geo.get("results") or []
            if not results:
                raise WeatherError("شهر پیدا نشد")
            location = results[0]
            lat = location["latitude"]
            lon = location["longitude"]

            weather_response = await self._client.get(
                self._WEATHER_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current_weather": "true",
                    "timezone": "auto",
                },
            )
            weather_response.raise_for_status()
            current = weather_response.json().get("current_weather", {})
        except httpx.RequestError as exc:
            raise WeatherError("سرویس آب‌وهوا در دسترس نیست") from exc

        weather_code = current.get("weathercode", 0)
        return WeatherInfo(
            temperature=float(current.get("temperature", 0.0)),
            feels_like=None,
            description=_describe_wmo_code(weather_code),
            humidity=int(current.get("relative_humidity") or 0) or None,
            wind_speed=float(current.get("windspeed", 0.0)),
            city=location.get("name", city),
            country_code=location.get("country_code"),
        )


class CachedWeatherService:
    """Weather service that caches responses for a short time."""

    def __init__(self, provider: WeatherProvider | None = None, ttl: int = CACHE_TTL_SECONDS) -> None:
        self.provider = provider or OpenMeteoProvider()
        self._ttl = ttl
        self._cache: dict[str, tuple[float, WeatherInfo]] = {}

    async def fetch(self, city: str) -> WeatherInfo:
        normalized = city.strip().lower()
        now = time()
        cached = self._cache.get(normalized)
        if cached and now - cached[0] < self._ttl:
            return cached[1]
        info = await self.provider.get_weather(city)
        self._cache[normalized] = (now, info)
        return info


def _describe_wmo_code(code: int) -> str:
    descriptions = {
        0: "آسمان صاف",
        1: "نیمه‌ابری",
        2: "ابری",
        3: "ابری کامل",
        45: "مه",
        48: "مه و یخبندان",
        51: "باران ملایم",
        53: "باران خفیف",
        55: "باران",
        61: "بارش خفیف",
        63: "بارش متوسط",
        65: "بارش شدید",
        71: "برف خفیف",
        73: "برف",
        75: "برف سنگین",
        80: "رگبار",
        81: "رگبار متوسط",
        82: "رگبار شدید",
        95: "طوفان رعدوبرقی",
        96: "طوفان با تگرگ",
        99: "طوفان شدید با تگرگ",
    }
    return descriptions.get(code, "شرایط نامشخص")


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------
def create_weather_service(api_key: str | None = None) -> CachedWeatherService:
    """Create a cached weather service with the best available provider."""
    return CachedWeatherService(OpenMeteoProvider())
