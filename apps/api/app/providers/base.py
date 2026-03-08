from typing import Any, Protocol


class AIProvider(Protocol):
    name: str

    def summarize(self, text: str) -> str: ...


class SearchProvider(Protocol):
    name: str

    def search(self, query: str) -> list[dict[str, Any]]: ...


class ScraperProvider(Protocol):
    name: str

    def fetch(self, url: str) -> dict[str, Any]: ...


class GeocodeProvider(Protocol):
    name: str

    def geocode(self, query: str) -> tuple[float, float] | None: ...


class MediaAnalysisProvider(Protocol):
    name: str

    def analyze(self, media_url: str) -> dict[str, Any]: ...
