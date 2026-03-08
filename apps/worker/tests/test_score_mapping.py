from worker_app.scoring import map_score_to_status


def test_score_threshold_mapping() -> None:
    assert map_score_to_status(0.1, 0.0, 0.0) == "noise"
    assert map_score_to_status(0.3, 0.0, 0.0) == "rumor"
    assert map_score_to_status(0.48, 0.0, 0.0) == "developing"
    assert map_score_to_status(0.62, 0.0, 0.0) == "likely"
    assert map_score_to_status(0.76, 0.0, 0.0) == "credible"
    assert map_score_to_status(0.86, 0.0, 0.0) == "confirmed"
    assert map_score_to_status(0.95, 0.0, 0.0) == "officially_confirmed"


def test_penalties_override_score() -> None:
    assert map_score_to_status(0.95, 0.45, 0.1) == "disputed"
    assert map_score_to_status(0.95, 0.1, 0.8) == "false"
