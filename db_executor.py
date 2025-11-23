"""
数据库执行模块
功能：连接并执行只读查询与执行计划（仅 MySQL）。
方法：
- query(db_url, sql, timeout, row_limit): 执行只读查询并返回行与列
- explain(db_url, sql): 返回查询执行计划
"""
from urllib.parse import urlparse

class DbExecutor:
    def query(self, db_url: str, sql: str, timeout: int, row_limit: int):
        
        if db_url.startswith("mysql://"):
            parsed = urlparse(db_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 3306
            user = parsed.username or "root"
            password = parsed.password or ""
            db = (parsed.path or "/").lstrip("/")
            try:
                import pymysql
            except Exception as e:
                raise RuntimeError("MySQL execution requires 'pymysql' to be installed") from e
            conn = pymysql.connect(host=host, port=port, user=user, password=password, database=db, charset="utf8mb4")
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            headers = [c[0] for c in cur.description]
            conn.close()
            return rows, headers
        raise RuntimeError("Unsupported DB_URL. Please use mysql://...")
    def explain(self, db_url: str, sql: str):
        
        if db_url.startswith("mysql://"):
            parsed = urlparse(db_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 3306
            user = parsed.username or "root"
            password = parsed.password or ""
            db = (parsed.path or "/").lstrip("/")
            try:
                import pymysql
            except Exception as e:
                raise RuntimeError("MySQL execution requires 'pymysql' to be installed") from e
            conn = pymysql.connect(host=host, port=port, user=user, password=password, database=db, charset="utf8mb4")
            cur = conn.cursor()
            cur.execute("EXPLAIN " + sql)
            rows = cur.fetchall()
            headers = [c[0] for c in cur.description]
            conn.close()
            return rows, headers
        raise RuntimeError("Unsupported DB_URL. Please use mysql://...")