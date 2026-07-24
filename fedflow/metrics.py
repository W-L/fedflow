from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
import json
from pathlib import Path
import shutil
import resource
import time
from typing import Any, Iterator




class MetricsRecorder:
    def __init__(self, config_path: str, outdir: str, stamp: str, log_path: str):
        self.config_path = config_path
        self.outdir = Path(outdir)
        self.stamp = stamp
        self.log_path = log_path
        self.started_at = datetime.now().isoformat(timespec="seconds")
        self._wall_start = time.perf_counter()
        self._cpu_start = time.process_time()
        self.metadata: dict[str, Any] = {}
        self.counters: dict[str, float] = defaultdict(float)
        self.phases: list[dict[str, Any]] = []


    @contextmanager
    def phase(self, name: str, **details: Any) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            phase = {
                "name": name,
                "duration_seconds": round(duration, 6),
            }
            if details:
                phase["details"] = details
            self.phases.append(phase)


    def set_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value


    def increment(self, key: str, value: int | float) -> None:
        self.counters[key] += value


    def write(self, status: str = "completed", error: str | None = None) -> Path:
        finished_at = datetime.now().isoformat(timespec="seconds")
        total_wall = time.perf_counter() - self._wall_start
        total_cpu = time.process_time() - self._cpu_start
        payload = {
            "status": status,
            "started_at": self.started_at,
            "finished_at": finished_at,
            "config_path": self.config_path,
            "log_path": self.log_path,
            "metadata": self.metadata,
            "phases": self.phases,
            "counters": dict(sorted(self.counters.items())),
            "resources": {
                "wall_clock_seconds": round(total_wall, 6),
                "process_cpu_seconds": round(total_cpu, 6),
                "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            },
        }
        if error is not None:
            payload["error"] = error

        self.outdir.mkdir(parents=True, exist_ok=True)
        metrics_path = self.outdir / f"fedflow_metrics_{self.stamp}.json"
        with metrics_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        latest_path = self.outdir / "fedflow_metrics.json"
        shutil.copy2(metrics_path, latest_path)
        return metrics_path
    
    