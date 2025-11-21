"""
数据库执行模块
功能：连接并执行只读查询与执行计划（MySQL/SQL Server）。
方法：
- query(db_url, sql, timeout, row_limit): 执行只读查询并返回行与列
- explain(db_url, sql): 返回查询执行计划
"""
from urllib.parse import urlparse, parse_qs

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
        if db_url.startswith("mssql://"):
            parsed = urlparse(db_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 1433
            user = parsed.username or "sa"
            password = parsed.password or ""
            db = (parsed.path or "/").lstrip("/")
            qs = parse_qs(parsed.query or "")
            preferred = (qs.get("driver", [None]))[0]
            instance = (qs.get("instance", [None]))[0]
            try:
                import pyodbc
            except Exception as e:
                raise RuntimeError("SQL Server execution requires 'pyodbc' to be installed") from e
            candidates = [d for d in [preferred, "ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"] if d]
            last_err = None
            server_specs = []
            if instance:
                server_specs.append(f"{host}\\{instance}")
            server_specs.extend([f"{host},{port}", f"{host};PORT={port}", f"{host}"])
            for driver in candidates:
                for server in server_specs:
                    for extra in ("", ";Encrypt=no;TrustServerCertificate=yes"):
                        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={db};UID={user};PWD={password}{extra}"
                        try:
                            conn = pyodbc.connect(conn_str)
                            cur = conn.cursor()
                            cur.execute(sql)
                            rows = cur.fetchall()
                            headers = [d[0] for d in (cur.description or [])]
                            conn.close()
                            return rows, headers
                        except Exception as e:
                            last_err = e
                            continue
            raise last_err or RuntimeError("Failed to connect SQL Server with available drivers")
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
        if db_url.startswith("mssql://"):
            parsed = urlparse(db_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 1433
            user = parsed.username or "sa"
            password = parsed.password or ""
            db = (parsed.path or "/").lstrip("/")
            qs = parse_qs(parsed.query or "")
            preferred = (qs.get("driver", [None]))[0]
            instance = (qs.get("instance", [None]))[0]
            try:
                import pyodbc
            except Exception as e:
                raise RuntimeError("SQL Server execution requires 'pyodbc' to be installed") from e
            candidates = [d for d in [preferred, "ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"] if d]
            last_err = None
            server_specs = []
            if instance:
                server_specs.append(f"{host}\\{instance}")
            server_specs.extend([f"{host},{port}", f"{host};PORT={port}", f"{host}"])
            for driver in candidates:
                for server in server_specs:
                    for extra in ("", ";Encrypt=no;TrustServerCertificate=yes"):
                        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={db};UID={user};PWD={password}{extra}"
                        try:
                            conn = pyodbc.connect(conn_str)
                            cur = conn.cursor()
                            try:
                                cur.execute("SET SHOWPLAN_TEXT ON")
                                cur.execute(sql)
                                rows = cur.fetchall()
                            finally:
                                try:
                                    cur.execute("SET SHOWPLAN_TEXT OFF")
                                except Exception:
                                    pass
                            headers = [d[0] for d in (cur.description or [])] or ["Plan"]
                            conn.close()
                            return rows, headers
                        except Exception as e:
                            last_err = e
                            continue
            raise last_err or RuntimeError("Failed to connect SQL Server with available drivers")
        raise RuntimeError("Unsupported DB_URL. Please use mysql://...")