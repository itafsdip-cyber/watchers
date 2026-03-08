from app.providers.registry import build_provider_registry


def test_unknown_provider_falls_back_to_default_local_stack() -> None:
    registry = build_provider_registry(
        default_ai_provider="not-real",
        default_search_provider="not-real",
        default_scraper_provider="not-real",
        default_geocode_provider="not-real",
        default_media_provider="not-real",
    )

    assert registry.active_names() == {
        "ai": "local",
        "search": "open",
        "scraper": "basic",
        "geocode": "nominatim",
        "media": "local",
    }


def test_paid_provider_requires_key_and_falls_back_without_key() -> None:
    registry = build_provider_registry(
        default_ai_provider="openai",
        default_search_provider="serpapi",
        default_scraper_provider="firecrawl",
        default_geocode_provider="google_maps",
        openai_api_key="",
        anthropic_api_key="",
        gemini_api_key="",
        serpapi_api_key="",
        firecrawl_api_key="",
        google_maps_api_key="",
    )

    assert registry.active_names() == {
        "ai": "local",
        "search": "open",
        "scraper": "basic",
        "geocode": "nominatim",
        "media": "local",
    }
