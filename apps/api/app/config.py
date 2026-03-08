from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Watchers API"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://watchers:watchers@localhost:5432/watchers"
    default_ai_provider: str = "local"
    default_search_provider: str = "open"
    default_scraper_provider: str = "basic"
    default_geocode_provider: str = "nominatim"
    default_media_provider: str = "local"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    serpapi_api_key: str = ""
    firecrawl_api_key: str = ""
    google_maps_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
