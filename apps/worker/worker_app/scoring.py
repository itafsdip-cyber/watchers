from dataclasses import dataclass


@dataclass
class ScoreResult:
    final_score: float
    status: str
    dimensions: dict[str, float]


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def map_score_to_status(score: float, contradiction_penalty: float, manipulation_penalty: float) -> str:
    if contradiction_penalty >= 0.7 or manipulation_penalty >= 0.7:
        return "false"
    if contradiction_penalty >= 0.4 or manipulation_penalty >= 0.4:
        return "disputed"
    if score < 0.20:
        return "noise"
    if score < 0.35:
        return "rumor"
    if score < 0.50:
        return "developing"
    if score < 0.65:
        return "likely"
    if score < 0.78:
        return "credible"
    if score < 0.90:
        return "confirmed"
    return "officially_confirmed"


def score_claim(claim: dict) -> ScoreResult:
    sources = claim.get("sources", [])
    source_reliability = clamp(
        sum(float(s.get("reliability", 0.5)) for s in sources) / len(sources) if sources else 0.3
    )

    independent_reports = int(claim.get("independent_reports", 1))
    evidence_count = int(claim.get("evidence_count", 0))
    cross_hits = int(claim.get("cross_platform_hits", 1))

    dimensions = {
        "source_reliability": source_reliability,
        "independence": clamp(0.2 + independent_reports * 0.15),
        "evidence_strength": clamp(0.2 + evidence_count * 0.1),
        "temporal_consistency": clamp(float(claim.get("temporal_consistency", 0.6))),
        "geographic_consistency": clamp(float(claim.get("geographic_consistency", 0.6))),
        "cross_platform_consistency": clamp(0.2 + cross_hits * 0.12),
        "historical_source_accuracy": clamp(float(claim.get("historical_source_accuracy", source_reliability))),
        "contradiction_penalty": clamp(float(claim.get("contradiction_signals", 0.0))),
        "manipulation_penalty": clamp(float(claim.get("manipulation_signals", 0.0))),
    }

    weighted_positive = (
        dimensions["source_reliability"] * 0.20
        + dimensions["independence"] * 0.15
        + dimensions["evidence_strength"] * 0.15
        + dimensions["temporal_consistency"] * 0.10
        + dimensions["geographic_consistency"] * 0.10
        + dimensions["cross_platform_consistency"] * 0.10
        + dimensions["historical_source_accuracy"] * 0.20
    )
    penalty = dimensions["contradiction_penalty"] * 0.20 + dimensions["manipulation_penalty"] * 0.20
    final_score = clamp(weighted_positive - penalty)

    status = map_score_to_status(
        score=final_score,
        contradiction_penalty=dimensions["contradiction_penalty"],
        manipulation_penalty=dimensions["manipulation_penalty"],
    )

    rounded = {k: round(v, 3) for k, v in dimensions.items()}
    return ScoreResult(final_score=round(final_score, 3), status=status, dimensions=rounded)
