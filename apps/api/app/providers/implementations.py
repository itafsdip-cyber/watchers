from typing import Any


class LocalAIProvider:
    name = "local"

    def summarize(self, text: str) -> str:
        return text[:240]


class OpenAIAIProvider(LocalAIProvider):
    name = "openai"


class AnthropicAIProvider(LocalAIProvider):
    name = "anthropic"


class GeminiAIProvider(LocalAIProvider):
    name = "gemini"


class OpenSearchProvider:
    name = "open"

    def search(self, query: str) -> list[dict[str, Any]]:
        return [{"query": query, "provider": self.name, "results": []}]


class SerpApiSearchProvider(OpenSearchProvider):
    name = "serpapi"


class BasicScraperProvider:
    name = "basic"

    def fetch(self, url: str) -> dict[str, Any]:
        return {"url": url, "provider": self.name, "content": ""}


class FirecrawlScraperProvider(BasicScraperProvider):
    name = "firecrawl"


class NominatimGeocodeProvider:
    name = "nominatim"

    def geocode(self, query: str) -> tuple[float, float] | None:
        return None


class GoogleMapsGeocodeProvider(NominatimGeocodeProvider):
    name = "google_maps"


class LocalMediaAnalysisProvider:
    name = "local"

    def analyze(self, media_url: str) -> dict[str, Any]:
        return {
            "provider": self.name,
            "media_url": media_url,
            "manipulation_risk": 0.0,
            "notes": ["MVP local stub: no external media analysis called."],
        }
