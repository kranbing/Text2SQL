from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
from typing import Optional
from fastapi.staticfiles import StaticFiles
from text2sql.orchestrator import Orchestrator
from .state import add_history, list_history, create_task, update_task, get_task, run_batch
from urllib.parse import urlparse

class ChatConfig(BaseModel):
    show_schema_insight: bool = True
    execute_sql: bool = True
    export_json: bool = False
    use_rag: bool = True

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    config: ChatConfig
    limit: Optional[int] = None

class ConfigUpdate(BaseModel):
    db_url: Optional[str] = None
    dialect: Optional[str] = None
    kb_dir: Optional[str] = None
    kb_glob: Optional[str] = None

app = FastAPI()

origins = [os.getenv("FRONTEND_ORIGIN", "http://localhost:8000"), "http://127.0.0.1:8000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

downloads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
app.mount("/v1/downloads", StaticFiles(directory=downloads_dir), name="downloads")

def _load_env_file():
    base = os.path.dirname(os.path.dirname(__file__))
    env_path = os.path.join(base, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith("#"):
                        continue
                    if "=" in s:
                        k, v = s.split("=", 1)
                        k = k.strip()
                        v = v.strip()
                        if k and v and (os.getenv(k) is None):
                            os.environ[k] = v
        except Exception:
            pass

_load_env_file()
orchestrator = Orchestrator()

@app.post("/v1/chat/completion")
def chat_completion(req: ChatRequest):
    limit = req.limit or 100
    explain = getattr(req.config, "explain", False)
    dry_run = not req.config.execute_sql
    res = orchestrator.run_to_result(req.message, limit=limit, explain=explain, dry_run=dry_run, show_schema=req.config.show_schema_insight)
    sql = res.get("sql")
    data = {
        "sql_query": sql or "",
        "explanation": "",
        "query_result": None,
        "exports": {"json_url": None},
        "metadata": {"tables_involved": [], "execution_time_ms": 0}
    }
    if res.get("plan_rows") and res.get("plan_headers"):
        data["plan"] = {"columns": res.get("plan_headers"), "rows": [list(r) for r in res.get("plan_rows") or []]}
    if sql:
        rows = res.get("rows") or []
        headers = res.get("headers") or []
        data["query_result"] = {"columns": headers, "rows": [list(r) for r in rows]}
        if req.config.export_json and rows:
            p = orchestrator.out.save_json(req.message, sql, rows, headers)
            data["exports"]["json_url"] = "/v1/downloads/" + os.path.basename(p)
    add_history({"id": uuid.uuid4().hex, "query_text": req.message, "sql_generated": sql or "", "created_at": __import__("datetime").datetime.utcnow().isoformat() + "Z"})
    return {"code": 200, "status": "success", "data": data}


@app.get("/v1/user/history")
def get_history(page: int = 1, limit: int = 10):
    items = list_history(page, limit)
    return {"code": 200, "data": items}

@app.post("/v1/tools/upload")
async def upload(file: UploadFile = File(...), task_type: str = Form(...)):
    project_root = os.path.dirname(os.path.dirname(__file__))
    upload_dir = os.path.join(os.path.dirname(project_root), "upload")
    os.makedirs(upload_dir, exist_ok=True)
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    out_path = os.path.join(upload_dir, task_id + "_" + (file.filename or "upload.bin"))
    with open(out_path, "wb") as f:
        f.write(await file.read())
    create_task(task_id, task_type)
    if task_type == "batch_query":
        import threading
        t = threading.Thread(target=run_batch, args=(orchestrator, out_path, task_id))
        t.daemon = True
        t.start()
    else:
        kb_dir = os.path.join(os.path.dirname(project_root), "upload")
        os.makedirs(kb_dir, exist_ok=True)
        dst = os.path.join(kb_dir, file.filename)
        try:
            os.replace(out_path, dst)
        except Exception:
            pass
        update_task(task_id, status="completed", progress=100)
    return {"code": 200, "message": "文件上传成功，任务处理中", "data": {"task_id": task_id, "status": "processing", "estimated_time": "30s"}}

@app.get("/v1/tools/task/{task_id}")
def get_task_status(task_id: str):
    t = get_task(task_id) or {"task_id": task_id, "status": "failed", "progress": 0}
    return {"code": 200, "data": t}

@app.get("/v1/rag/show")
def show_rag():
    project_root = os.path.dirname(os.path.dirname(__file__))
    kb_dir = orchestrator.kb_dir or os.getenv("KB_DIR", None) or os.path.join(os.path.dirname(project_root), "upload")
    if not kb_dir or not os.path.isdir(kb_dir):
        return {"code": 200, "data": {"count": 0, "files": [], "previews": []}}
    files = []
    count = 0
    try:
        text_exts = {".txt", ".md", ".json", ".csv", ".xml", ".py", ".sql", ".log", ".ini", ".cfg"}
        for root, _, fnames in os.walk(kb_dir):
            for fn in fnames:
                count += 1
                full = os.path.join(root, fn)
                ext = os.path.splitext(fn)[1].lower()
                preview = ""
                if ext in text_exts:
                    try:
                        with open(full, "r", encoding="utf-8", errors="ignore") as f:
                            t = f.read(1000).replace("\r", " ").replace("\n", " ")
                            preview = (t[:120] + "...") if len(t) > 120 else t
                    except Exception:
                        preview = "不可预览"
                else:
                    preview = "二进制或不可预览文件"
                files.append({"name": fn, "preview": preview})
            break
    except Exception:
        pass
    return {"code": 200, "data": {"count": count, "files": files}}

@app.get("/v1/database/info")
def database_info():
    info = orchestrator.get_database_info()
    return {"code": 200, "data": info}

@app.get("/v1/database/schema")
def database_schema():
    try:
        db_url = orchestrator.db_url
        dialect = orchestrator.dialect or "mysql"
        schema = orchestrator.schema.load(db_url, dialect)
        tables = []
        for t, cols in (schema.get("tables") or {}).items():
            tables.append({"table_name": t, "columns": [{"name": c, "type": "", "is_primary": False} for c in cols]})
        return {"code": 200, "data": {"tables": tables}}
    except Exception as e:
        return {"code": 500, "message": str(e)}

@app.post("/v1/config/update")
def config_update(cfg: ConfigUpdate):
    orchestrator.update_config(db_url=cfg.db_url, dialect=cfg.dialect, kb_dir=cfg.kb_dir, kb_glob=cfg.kb_glob)
    return {"code": 200, "status": "success"}