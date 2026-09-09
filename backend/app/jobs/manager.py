"""
Lightweight background job system: a ThreadPoolExecutor plus a JSON-backed
status store. This is intentionally dependency-light (no Redis/Celery) so the
service runs on a single Render web instance out of the box. For heavier
production load, swap this module for Celery+Redis or RQ - `JobManager`'s
public interface (`submit`, `get`, `list`) is the only thing callers depend on.
"""
import json
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..config import get_settings
from ..services.security import new_job_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobManager:
    def __init__(self, store_path: str, max_workers: int):
        self._store_path = Path(store_path)
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._jobs: dict[str, dict] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._load()

    def _load(self) -> None:
        if self._store_path.exists():
            try:
                self._jobs = json.loads(self._store_path.read_text())
            except json.JSONDecodeError:
                self._jobs = {}

    def _persist(self) -> None:
        self._store_path.write_text(json.dumps(self._jobs, indent=2, default=str))

    def _update(self, job_id: str, **fields) -> None:
        with self._lock:
            self._jobs[job_id]["updated_at"] = _now()
            self._jobs[job_id].update(fields)
            self._persist()

    def report_progress(self, job_id: str, stage: str, progress_pct: int | None = None, message: str = "") -> None:
        self._update(job_id, stage=stage, progress_pct=progress_pct, message=message, status="processing")

    def submit(self, task_fn: Callable[[str, "JobManager"], list[str]]) -> str:
        job_id = new_job_id()
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id, "status": "queued", "stage": "preparing",
                "progress_pct": 0, "message": "Queued", "created_at": _now(),
                "updated_at": _now(), "result_files": [], "error": None,
            }
            self._persist()

        def _run():
            try:
                self._update(job_id, status="processing", stage="preparing", message="Starting extraction")
                result_files = task_fn(job_id, self)
                self._update(job_id, status="completed", stage="complete", progress_pct=100,
                             message="Extraction complete", result_files=result_files)
            except Exception as e:  # noqa: BLE001
                self._update(job_id, status="failed", stage="failed",
                             message="Extraction failed", error=f"{e}\n{traceback.format_exc()}")

        self._executor.submit(_run)
        return job_id

    def get(self, job_id: str) -> dict | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> list[dict]:
        with self._lock:
            return list(self._jobs.values())


_manager: JobManager | None = None


def get_job_manager() -> JobManager:
    global _manager
    if _manager is None:
        s = get_settings()
        _manager = JobManager(s.JOB_STORE_PATH, s.MAX_WORKERS)
    return _manager
