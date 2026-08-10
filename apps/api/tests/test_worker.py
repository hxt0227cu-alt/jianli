import json

from app.config import Settings
from app.worker import run_worker


def test_worker_smoke_logs_one_safe_structured_event(capsys, monkeypatch) -> None:
    monkeypatch.setenv("JIANLI_SECRET_TOKEN", "do-not-log")

    exit_code = run_worker(Settings(log_level="INFO"))

    output = capsys.readouterr().err.strip().splitlines()
    assert exit_code == 0
    assert len(output) == 1
    record = json.loads(output[0])
    assert record["event"] == "worker_smoke_completed"
    assert record["logger"] == "jianli.worker"
    assert "do-not-log" not in output[0]
