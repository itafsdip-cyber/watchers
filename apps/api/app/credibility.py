from app.models import Incident


def build_explanation(incident: Incident) -> tuple[dict[str, float], list[str]]:
    source_scores = [s.reliability_score for s in incident.sources]
    source_reliability = sum(source_scores) / len(source_scores) if source_scores else 0.3

    dimensions = {
        "source_reliability": round(source_reliability, 3),
        "independence": min(1.0, 0.3 + (len(incident.sources) * 0.15)),
        "evidence_strength": min(1.0, 0.2 + (len(incident.timeline_entries) * 0.1)),
        "temporal_consistency": 0.7,
        "geographic_consistency": 0.7 if incident.latitude is not None and incident.longitude is not None else 0.4,
        "cross_platform_consistency": 0.6,
        "historical_source_accuracy": source_reliability,
        "contradiction_penalty": 0.0,
        "manipulation_penalty": 0.0,
    }

    notes = [
        "Scores are transparent MVP heuristics.",
        "Penalties remain zero until contradiction/manipulation signals are detected.",
    ]
    return dimensions, notes
