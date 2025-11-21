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

    def run(self, question: str, limit: int, explain: bool, dry_run: bool, as_json: bool = False, as_csv: bool = False, show_schema: bool = False):
        db_url = self.db_url
        # 自动根据 URL scheme 选择方言
        if db_url.startswith("mssql://"):
            dialect = "mssql"
        else:
            dialect = "mysql"
        if not db_url:
            raise RuntimeError("Missing DB_URL. Please set MySQL connection string, e.g., mysql://user:pass@host:3306/db")
        schema = self.schema.load(db_url, dialect)

        if show_schema:
            for t, cols in schema.get("tables", {}).items():
                print(f"{t}: {', '.join(cols)}")
        docs = schema.get("docs", [])
        self.rag_index.build(docs)
        self.rag.set_index(self.rag_index)
        ctx_docs = self.rag.query(question, top_k=5)

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
            print(p)
            return
        
        if as_csv:
            p = self.out.save_csv(question, sql, rows, headers)
            print(p)
            return
        
        print(sql)
        print(self.out.to_table(rows, headers))
        if plan_rows and plan_headers:
            print(self.out.to_table(plan_rows, plan_headers))