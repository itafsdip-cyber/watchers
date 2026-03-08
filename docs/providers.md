# Provider Abstraction

## Interfaces
Defined in `apps/api/app/providers/base.py`:
- `AIProvider`
- `SearchProvider`
- `ScraperProvider`
- `GeocodeProvider`
- `MediaAnalysisProvider`

## Default Local/Open Providers
- AI: `local`
- Search: `open`
- Scraper: `basic`
- Geocode: `nominatim`
- Media: `local`

## Optional Paid Provider Placeholders
- AI: `openai`, `anthropic`, `gemini`
- Search: `serpapi`
- Scraper: `firecrawl`
- Geocode: `google_maps`

Without API keys, selection safely falls back to local/open providers.

## Env-Driven Selection
Use `.env` keys:
- `DEFAULT_AI_PROVIDER`
- `DEFAULT_SEARCH_PROVIDER`
- `DEFAULT_SCRAPER_PROVIDER`
- `DEFAULT_GEOCODE_PROVIDER`
- `DEFAULT_MEDIA_PROVIDER`

Active selection is visible via API endpoint `/providers/active`.
