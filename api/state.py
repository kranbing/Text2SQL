import os
import json
import threading
import time
from typing import Any

_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
os.makedirs(_base, exist_ok=True)

_history_path = os.path.join(_base, "history.json")
_tasks_path = os.path.join(_base, "tasks.json")

_lock = threading.Lock()
_tasks: dict[str, dict[str, Any]] = {}

def _load_json(path: str) -> Any:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _save_json(path: str, data: Any):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def add_history(item: dict):
    with _lock:
        data = _load_json(_history_path) or []
        data.insert(0, item)
        if len(data) > 500:
            data = data[:500]
        _save_json(_history_path, data)

def list_history(page: int, limit: int) -> list[dict]:
    data = _load_json(_history_path) or []
    start = (page - 1) * limit
    end = start + limit
    return data[start:end]

def create_task(task_id: str, task_type: str):
    with _lock:
        _tasks[task_id] = {"task_id": task_id, "task_type": task_type, "status": "processing", "progress": 0, "result_url": None}
        _save_json(_tasks_path, _tasks)

def update_task(task_id: str, **kwargs):
    with _lock:
        if task_id in _tasks:
            _tasks[task_id].update(kwargs)
            _save_json(_tasks_path, _tasks)

def get_task(task_id: str) -> dict | None:
    with _lock:
        return _tasks.get(task_id)

def run_batch(orchestrator, file_path: str, task_id: str, limit: int = 100):
    try:
        update_task(task_id, progress=10)
        orchestrator.run_batch_file(file_path, limit, as_json=True)
        update_task(task_id, status="completed", progress=100)
    except Exception:
        update_task(task_id, status="failed", progress=100)