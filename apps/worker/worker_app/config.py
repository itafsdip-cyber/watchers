from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://watchers:watchers@localhost:5432/watchers"
    sample_claims_path: str = "../../data/samples/raw_claims.json"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
