"""
Schema 提供模块
功能：读取数据库结构并生成检索文档，支持 MySQL/SQL Server；导入 JSON 数据并校验；输出 db_info JSON。
方法：
- load(db_url, dialect): 加载并返回 {tables, docs}
- import_json(file_path, db_url, dialect): 导入 JSON 到数据库
- _write_db_info(db_url, schema): 写入 db_info 文件
- _ensure_mysql_table(cur, table_name, columns): 创建表
- _insert_mysql(cur, table_name, columns, row): 插入行
- _validate_and_normalize_row(row, columns): 校验与规范化
"""
import os
from urllib.parse import urlparse
import json
import re

class SchemaProvider:
    def load(self, db_url: str, dialect: str) -> dict:
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
                raise RuntimeError("MySQL schema introspection requires 'pymysql' to be installed") from e
            conn = pymysql.connect(host=host, port=port, user=user, password=password, database=db, charset="utf8mb4")
            cur = conn.cursor()
            cur.execute("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema=%s ORDER BY table_name, ordinal_position", (db,))
            tables = {}
            docs = []
            for t, c in cur.fetchall():
                tables.setdefault(t, []).append(c)
            for t, cols in tables.items():
                docs.append(f"table {t}: " + ", ".join(cols))
            conn.close()
            try:
                self._write_db_info(db_url, {"tables": tables, "docs": docs})
            except Exception:
                pass
            return {"tables": tables, "docs": docs}
        if db_url.startswith("mssql://"):
            parsed = urlparse(db_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 1433
            user = parsed.username or "sa"
            password = parsed.password or ""
            db = (parsed.path or "/").lstrip("/")
            try:
                import pyodbc
            except Exception as e:
                raise RuntimeError("SQL Server schema introspection requires 'pyodbc' to be installed") from e
            conn = None
            drivers = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]
            server_specs = [f"{host},{port}", f"{host};PORT={port}", f"{host}"]
            last_err = None
            for d in drivers:
                for server in server_specs:
                    for extra in ("", ";Encrypt=no;TrustServerCertificate=yes"):
                        try:
                            conn = pyodbc.connect(f"DRIVER={{{d}}};SERVER={server};DATABASE={db};UID={user};PWD={password}{extra}")
                            break
                        except Exception as e:
                            last_err = e
                            conn = None
                            continue
                if conn:
                    break
            if conn is None:
                raise RuntimeError("Failed to connect SQL Server with available drivers")
            cur = conn.cursor()
            cur.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS ORDER BY TABLE_NAME, ORDINAL_POSITION")
            tables = {}
            docs = []
            for t, c in cur.fetchall():
                tables.setdefault(t, []).append(c)
            for t, cols in tables.items():
                docs.append(f"table {t}: " + ", ".join(cols))
            conn.close()
            try:
                self._write_db_info(db_url, {"tables": tables, "docs": docs})
            except Exception:
                pass
            return {"tables": tables, "docs": docs}
        raise RuntimeError("Unsupported DB_URL. Please use mysql://...")
    
    def import_json(self, file_path: str, db_url: str, dialect: str) -> dict:
        raise NotImplementedError("import_json feature is temporarily disabled")
    def _write_db_info(self, db_url: str, schema: dict):
        parsed = urlparse(db_url)
        db = (parsed.path or "/").lstrip("/")
        info_dir = os.path.join(os.path.dirname(__file__), "db_info")
        os.makedirs(info_dir, exist_ok=True)
        out_path = os.path.join(info_dir, f"{db}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"db": db, "host": parsed.hostname, "port": parsed.port, "tables": schema.get("tables", {}), "docs": schema.get("docs", [])}, f, ensure_ascii=False)
    def _ensure_mysql_table(self, cur, table_name: str, columns: list):
        defs = []
        for c in columns:
            name = c["name"]
            typ = c.get("type", "string").lower()
            if typ in ("integer", "int"):
                defs.append(f"{name} INT")
            elif typ in ("float", "double", "real"):
                defs.append(f"{name} DOUBLE")
            elif typ in ("date", "datetime"):
                defs.append(f"{name} VARCHAR(32)")
            else:
                defs.append(f"{name} VARCHAR(255)")
        cur.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (" + ", ".join(defs) + ")")
    def _insert_mysql(self, cur, table_name: str, columns: list, row: dict):
        names = [c["name"] for c in columns]
        placeholders = ", ".join(["%s"] * len(names))
        vals = [row.get(n) for n in names]
        cur.execute(f"INSERT INTO {table_name} (" + ", ".join(names) + ") VALUES (" + placeholders + ")", vals)
    def _validate_and_normalize_row(self, row: dict, columns: list):
        out = {}
        for c in columns:
            name = c.get("name")
            typ = c.get("type", "string").lower()
            required = bool(c.get("required", False))
            max_len = c.get("max_length")
            pattern = c.get("pattern")
            fmt = c.get("format")
            val = row.get(name)
            if required and (val is None or (isinstance(val, str) and val.strip() == "")):
                return False, None, f"missing required {name}"
            if val is None:
                out[name] = None
                continue
            if isinstance(val, str):
                val = val.strip()
            try:
                if typ in ("integer", "int"):
                    if isinstance(val, str) and val.isdigit():
                        val = int(val)
                    elif isinstance(val, (int,)):
                        val = int(val)
                    else:
                        return False, None, f"invalid integer {name}"
                elif typ in ("float", "double", "real"):
                    val = float(val)
                elif typ in ("date", "datetime"):
                    if fmt == "YYYY-MM-DD":
                        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(val)):
                            return False, None, f"invalid date {name}"
                    else:
                        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(val)):
                            return False, None, f"invalid date {name}"
                else:
                    if max_len and isinstance(val, str) and len(val) > int(max_len):
                        val = val[: int(max_len)]
                    if pattern and isinstance(val, str) and not re.match(pattern, val):
                        return False, None, f"pattern mismatch {name}"
            except Exception:
                return False, None, f"type conversion failed {name}"
            out[name] = val
        return True, out, None