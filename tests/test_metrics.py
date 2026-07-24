import json

from fedflow.metrics import MetricsRecorder


def test_metrics_recorder_writes_artifact(tmp_path):
    recorder = MetricsRecorder(
        config_path="conf/config.toml",
        outdir=str(tmp_path),
        stamp="20260720-120000",
        log_path="20260720-120000_fedflow.log",
    )

    recorder.set_metadata("client_count", 3)
    recorder.increment("distributed_input_bytes", 128)
    with recorder.phase("connect_clients"):
        pass

    metrics_path = recorder.write()

    assert metrics_path.exists()
    assert (tmp_path / "fedflow_metrics.json").exists()
    payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert payload["status"] == "completed"
    assert payload["metadata"]["client_count"] == 3
    assert payload["counters"]["distributed_input_bytes"] == 128
    assert payload["phases"][0]["name"] == "connect_clients"
    assert payload["resources"]["wall_clock_seconds"] >= 0


def test_metrics_recorder_captures_failure(tmp_path):
    recorder = MetricsRecorder(
        config_path="conf/config.toml",
        outdir=str(tmp_path),
        stamp="20260720-120001",
        log_path="20260720-120001_fedflow.log",
    )

    metrics_path = recorder.write(status="failed", error="oops")
    payload = json.loads(metrics_path.read_text(encoding="utf-8"))

    assert payload["status"] == "failed"
    assert payload["error"] == "oops"