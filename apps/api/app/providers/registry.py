from dataclasses import dataclass
from functools import lru_cache
from typing import TypeVar

from app.config import settings
from app.providers.base import AIProvider, GeocodeProvider, MediaAnalysisProvider, ScraperProvider, SearchProvider
from app.providers.implementations import (
    AnthropicAIProvider,
    BasicScraperProvider,
    FirecrawlScraperProvider,
    GeminiAIProvider,
    GoogleMapsGeocodeProvider,
    LocalAIProvider,
    LocalMediaAnalysisProvider,
    NominatimGeocodeProvider,
    OpenAIAIProvider,
    OpenSearchProvider,
    SerpApiSearchProvider,
)

T = TypeVar("T")


@dataclass
class ProviderRegistry:
    ai: AIProvider
    search: SearchProvider
    scraper: ScraperProvider
    geocode: GeocodeProvider
    media: MediaAnalysisProvider

    def active_names(self) -> dict[str, str]:
        return {
            "ai": self.ai.name,
            "search": self.search.name,
            "scraper": self.scraper.name,
            "geocode": self.geocode.name,
            "media": self.media.name,
        }


def _pick(selected: str, options: dict[str, T], fallback: str) -> T:
    return options.get(selected.lower(), options[fallback])


def build_provider_registry(
    default_ai_provider: str | None = None,
    default_search_provider: str | None = None,
    default_scraper_provider: str | None = None,
    default_geocode_provider: str | None = None,
    default_media_provider: str | None = None,
    openai_api_key: str | None = None,
    anthropic_api_key: str | None = None,
    gemini_api_key: str | None = None,
    serpapi_api_key: str | None = None,
    firecrawl_api_key: str | None = None,
    google_maps_api_key: str | None = None,
) -> ProviderRegistry:
    ai_default = settings.default_ai_provider if default_ai_provider is None else default_ai_provider
    search_default = settings.default_search_provider if default_search_provider is None else default_search_provider
    scraper_default = settings.default_scraper_provider if default_scraper_provider is None else default_scraper_provider
    geocode_default = settings.default_geocode_provider if default_geocode_provider is None else default_geocode_provider
    media_default = settings.default_media_provider if default_media_provider is None else default_media_provider
    openai_key = settings.openai_api_key if openai_api_key is None else openai_api_key
    anthropic_key = settings.anthropic_api_key if anthropic_api_key is None else anthropic_api_key
    gemini_key = settings.gemini_api_key if gemini_api_key is None else gemini_api_key
    serpapi_key = settings.serpapi_api_key if serpapi_api_key is None else serpapi_api_key
    firecrawl_key = settings.firecrawl_api_key if firecrawl_api_key is None else firecrawl_api_key
    google_maps_key = settings.google_maps_api_key if google_maps_api_key is None else google_maps_api_key

    ai_options = {
        "local": LocalAIProvider(),
        "openai": OpenAIAIProvider() if openai_key else LocalAIProvider(),
        "anthropic": AnthropicAIProvider() if anthropic_key else LocalAIProvider(),
        "gemini": GeminiAIProvider() if gemini_key else LocalAIProvider(),
    }

    search_options = {
        "open": OpenSearchProvider(),
        "serpapi": SerpApiSearchProvider() if serpapi_key else OpenSearchProvider(),
    }

    scraper_options = {
        "basic": BasicScraperProvider(),
        "firecrawl": FirecrawlScraperProvider() if firecrawl_key else BasicScraperProvider(),
    }

    geocode_options = {
        "nominatim": NominatimGeocodeProvider(),
        "google_maps": GoogleMapsGeocodeProvider() if google_maps_key else NominatimGeocodeProvider(),
    }

    media_options = {
        "local": LocalMediaAnalysisProvider(),
    }

    return ProviderRegistry(
        ai=_pick(ai_default, ai_options, "local"),
        search=_pick(search_default, search_options, "open"),
        scraper=_pick(scraper_default, scraper_options, "basic"),
        geocode=_pick(geocode_default, geocode_options, "nominatim"),
        media=_pick(media_default, media_options, "local"),
    )


@lru_cache(maxsize=1)
def get_provider_registry() -> ProviderRegistry:
    return build_provider_registry()
