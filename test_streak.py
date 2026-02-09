from api import compute_streak

def test_empty():
    assert compute_streak([], "07:00", 10) == (0, 0)

def test_single_success():
    rows = [{"day": "2026-02-01", "wake_time": "06:55"}]
    assert compute_streak(rows, "07:00", 10) == (1, 1)

def test_single_fail():
    rows = [{"day": "2026-02-01", "wake_time": "07:30"}]
    assert compute_streak(rows, "07:00", 10) == (0, 0)

def test_gap_breaks_run():
    rows = [
        {"day": "2026-02-01", "wake_time": "06:55"},
        {"day": "2026-02-03", "wake_time": "06:55"},
    ]
    current, best = compute_streak(rows, "07:00", 10)
    assert best == 1
    assert current == 1

def test_best_longer_than_current():
    rows = [
        {"day": "2026-02-01", "wake_time": "06:55"},
        {"day": "2026-02-02", "wake_time": "06:55"},
        {"day": "2026-02-03", "wake_time": "07:30"},
        {"day": "2026-02-04", "wake_time": "06:55"},
    ]
    current, best = compute_streak(rows, "07:00", 10)
    assert best == 2
    assert current == 1

def test_boundary_is_success():
    rows = [{"day": "2026-02-01", "wake_time": "07:10"}]
    assert compute_streak(rows, "07:00", 10) == (1, 1)
