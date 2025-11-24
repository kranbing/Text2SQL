"""
编排模块
功能：整合 LLM、Schema、检索、护栏、执行与输出，完成一次查询流程。
方法：
- Orchestrator.run(question, limit, explain, dry_run, as_json, as_csv, show_schema): 执行查询并输出
"""
import os
import sys
import time
import threading
from llm_client import LLMClient
from schema_provider import SchemaProvider
from sql_guard import SqlGuard
from db_executor import DbExecutor
from output_formatter import OutputFormatter
from rag import RAGIndex, RAGRetriever

class Orchestrator:
    def __init__(self):
        self.llm = None
        self.schema = SchemaProvider()
        self.guard = SqlGuard()
        self.db = DbExecutor()
        self.out = OutputFormatter()
        self.rag_index = RAGIndex()
        self.rag = RAGRetriever()
        self.db_url = os.getenv("DB_URL", None)
        self.dialect = os.getenv("DIALECT", "mysql")
        self.kb_dir = os.getenv("KB_DIR", None)
        self.kb_glob = os.getenv("KB_GLOB", None)

    def run(self, question: str, limit: int, explain: bool, dry_run: bool, as_json: bool = False, as_csv: bool = False, show_schema: bool = False):
        db_url = self.db_url
        dialect = "mysql"
        if not db_url:
            raise RuntimeError("Missing DB_URL. Please set MySQL connection string, e.g., mysql://user:pass@host:3306/db")
        schema = self.schema.load(db_url, dialect)

        if show_schema:
            for t, cols in schema.get("tables", {}).items():
                print(f"{t}: {', '.join(cols)}")
        docs = schema.get("docs", [])
        kb_dir = self.kb_dir
        if kb_dir and os.path.isdir(kb_dir):
            kb_glob = self.kb_glob
            kb_docs = self.rag_index.load_docs_from_dir(kb_dir, kb_glob)
            docs = docs + kb_docs
        self.rag_index.build(docs)
        self.rag.set_index(self.rag_index)
        ctx_docs = self.rag.query(question, top_k=3)

        if self.llm is None:
            self.llm = LLMClient()
        stop_evt = threading.Event()
        def _spin():
            frames = "|/-\\"
            i = 0
            while not stop_evt.is_set():
                sys.stdout.write("\r正在调用模型 " + frames[i % len(frames)])
                sys.stdout.flush()
                time.sleep(0.1)
                i += 1
            sys.stdout.write("\r")
            sys.stdout.flush()
        t = threading.Thread(target=_spin, daemon=True)
        t.start()
        try:
            sql = self.llm.generate_sql(question, schema, dialect, limit, context_docs=ctx_docs)
        finally:
            stop_evt.set()
            t.join()
        if str(sql).strip() == "7355608":
            print("请检查要查询的字段是否在数据库中")
            return
        try:
            sql = self.guard.check_semantics(question, schema, sql)
        except ValueError:
            print("请检查要查询的字段是否在数据库中")
            return
        
        sql = self.guard.validate(sql, dialect)
        plan_rows, plan_headers = None, None

        if explain:
            plan_rows, plan_headers = self.db.explain(db_url, sql)

        if dry_run:
            print(sql)
            if plan_rows and plan_headers:
                print(self.out.to_table(plan_rows, plan_headers))
            return
        
        rows, headers = self.db.query(db_url, sql, timeout=30, row_limit=limit)
        if as_json:
            p = self.out.save_json(question, sql, rows, headers)
            print(f"文件保存到{p}")
            return
        
        
        print(sql)
        print(self.out.to_table(rows, headers))
        if plan_rows and plan_headers:
            print(self.out.to_table(plan_rows, plan_headers))

    def run_to_result(self, question: str, limit: int, explain: bool, dry_run: bool, show_schema: bool = False):
        db_url = self.db_url
        dialect = "mysql"
        if not db_url:
            raise RuntimeError("Missing DB_URL. Please set MySQL connection string, e.g., mysql://user:pass@host:3306/db")
        schema = self.schema.load(db_url, dialect)
        schema_tables = []
        if show_schema:
            for t, cols in schema.get("tables", {}).items():
                schema_tables.append({"table_name": t, "columns": [{"name": c, "type": ""} for c in cols]})
        docs = schema.get("docs", [])
        kb_dir = self.kb_dir
        if kb_dir and os.path.isdir(kb_dir):
            kb_glob = self.kb_glob
            kb_docs = self.rag_index.load_docs_from_dir(kb_dir, kb_glob)
            docs = docs + kb_docs
        self.rag_index.build(docs)
        self.rag.set_index(self.rag_index)
        ctx_docs = self.rag.query(question, top_k=3)
        if self.llm is None:
            self.llm = LLMClient()
        stop_evt = threading.Event()
        def _spin():
            frames = "|/-\\"
            i = 0
            while not stop_evt.is_set():
                time.sleep(0.1)
                i += 1
        t = threading.Thread(target=_spin, daemon=True)
        t.start()
        try:
            sql = self.llm.generate_sql(question, schema, dialect, limit, context_docs=ctx_docs)
        finally:
            stop_evt.set()
            t.join()
        if str(sql).strip() == "7355608":
            return {"sql": None, "rows": [], "headers": [], "metadata": {"tables_involved": [], "execution_time_ms": 0}}
        try:
            sql = self.guard.check_semantics(question, schema, sql)
        except ValueError:
            return {"sql": None, "rows": [], "headers": [], "metadata": {"tables_involved": [], "execution_time_ms": 0}}
        sql = self.guard.validate(sql, dialect)
        plan_rows, plan_headers = None, None
        if explain:
            plan_rows, plan_headers = self.db.explain(db_url, sql)
        rows, headers = [], []
        if not dry_run:
            rows, headers = self.db.query(db_url, sql, timeout=30, row_limit=limit)
        return {"sql": sql, "rows": rows, "headers": headers, "plan_rows": plan_rows, "plan_headers": plan_headers, "schema_tables": schema_tables}

    def show_rag(self):
        kb_dir = self.kb_dir or os.getenv("KB_DIR", None)
        if not kb_dir or not os.path.isdir(kb_dir):
            print("未配置 KB_DIR 或目录不存在")
            return
        kb_glob = self.kb_glob or os.getenv("KB_GLOB", None)
        kb_docs = self.rag_index.load_docs_from_dir(kb_dir, kb_glob)
        print(f"已导入知识库文档数：{len(kb_docs)}")
        for i, d in enumerate(kb_docs, 1):
            preview = d.strip().replace("\r", " ").replace("\n", " ")
            if len(preview) > 100:
                preview = preview[:100] + "..."
            print(f"[{i}] {preview}")

    def run_batch_file(self, filepath: str, limit: int, as_json: bool = False):
        db_url = self.db_url
        dialect = "mysql"
        if not db_url:
            raise RuntimeError("Missing DB_URL. Please set MySQL connection string, e.g., mysql://user:pass@host:3306/db")
        schema = self.schema.load(db_url, dialect)
        docs = schema.get("docs", [])
        kb_dir = self.kb_dir
        if kb_dir and os.path.isdir(kb_dir):
            kb_glob = self.kb_glob
            kb_docs = self.rag_index.load_docs_from_dir(kb_dir, kb_glob)
            docs = docs + kb_docs
        self.rag_index.build(docs)
        self.rag.set_index(self.rag_index)
        import json
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            print("文件格式错误：需要为json数组 [ {question: ...}, ... ]")
            return
        print(f"批量查询 {len(data)} 条")
        batch_items = []
        for i, item in enumerate(data, 1):
            try:
                if not isinstance(item, dict) or not item.get("question"):
                    print(f"[{i}] 跳过：缺少 question 字段")
                    batch_items.append({"question": item.get("question", ""), "error": "缺少question字段", "suggest": []})
                    continue
                q2 = str(item["question"]).strip()
                ctx_docs = self.rag.query(q2, top_k=3)
                if self.llm is None:
                    self.llm = LLMClient()
                sql = self.llm.generate_sql(q2, schema, dialect, limit, context_docs=ctx_docs)
                if str(sql).strip() == "7355608":
                    need = self.guard.suggest_missing_terms(q2, schema)
                    print(f"[{i}] 请检查要查询的字段是否在数据库中；可能需要提供：{', '.join(need) if need else '无'}")
                    batch_items.append({"question": q2, "sql": None, "rows": [], "headers": [], "error": "字段不在数据库中", "suggest": need})
                    continue
                try:
                    sql = self.guard.check_semantics(q2, schema, sql)
                except ValueError:
                    need = self.guard.suggest_missing_terms(q2, schema)
                    print(f"[{i}] 请检查要查询的字段是否在数据库中；可能需要提供：{', '.join(need) if need else '无'}")
                    batch_items.append({"question": q2, "sql": None, "rows": [], "headers": [], "error": "语义不匹配", "suggest": need})
                    continue
                sql = self.guard.validate(sql, dialect)
                rows, headers = self.db.query(db_url, sql, timeout=30, row_limit=limit)
                print(f"[{i}] {sql}")
                print(self.out.to_table(rows, headers))
                batch_items.append({"question": q2, "sql": sql, "rows": rows, "headers": headers, "error": None, "suggest": []})
            except Exception as e:
                need = self.guard.suggest_missing_terms(item.get("question", ""), schema)
                print(f"[{i}] 查询失败: {e}；可能需要提供：{', '.join(need) if need else '无'}")
                batch_items.append({"question": item.get("question", ""), "sql": None, "rows": [], "headers": [], "error": str(e), "suggest": need})
        if as_json:
            p = self.out.save_batch_json(batch_items)
            print(f"文件保存到{p}")
    
    def update_config(self, db_url: str | None = None, dialect: str | None = None, kb_dir: str | None = None, kb_glob: str | None = None):
        if db_url:
            self.db_url = db_url
        if dialect:
            self.dialect = dialect
        if kb_dir is not None:
            self.kb_dir = kb_dir
        if kb_glob is not None:
            self.kb_glob = kb_glob

    def get_database_info(self):
        url = self.db_url or ""
        host = ""
        database = ""
        try:
            from urllib.parse import urlparse
            u = urlparse(url)
            host = u.netloc
            p = (u.path or "/").lstrip("/")
            database = p
        except Exception:
            pass
        return {"dialect": self.dialect, "host": host, "database": database, "url": url}
