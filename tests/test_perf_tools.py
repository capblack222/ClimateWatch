import json

from perf.analyze_logs import load, nearest_rank


def test_nearest_rank():
    values = list(range(1, 101))
    assert nearest_rank(values, 50) == 50
    assert nearest_rank(values, 95) == 95
    assert nearest_rank(values, 99) == 99
    assert nearest_rank([7], 99) == 7


def test_load_groups_successful_requests_by_path_and_mode(tmp_path):
    log = tmp_path / "x.server.log"
    lines = [
        {"logger": "app.request", "path": "/weather", "status": 200, "duration_ms": 100, "upstream_ms": 90,
         "http_reuse": True},
        {"logger": "app.request", "path": "/weather", "status": 502, "duration_ms": 5, "http_reuse": True},
        {"logger": "app", "message": "Server starting"},
    ]
    log.write_text("\n".join(json.dumps(line) for line in lines) + "\nnot json\n")
    groups = load([str(log)])
    assert list(groups) == [("/weather", "reuse on")]
    assert len(groups[("/weather", "reuse on")]) == 1
