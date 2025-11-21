"""
SQL 护栏模块
功能：约束查询为只读单语句并追加默认 LIMIT。
方法：
- validate(sql, dialect): 返回安全的查询或抛出异常
"""
class SqlGuard:
    def validate(self, sql: str, dialect: str) -> str:
        s = sql.strip()
        l = s.lower()
        forbidden = ["delete", "update", "insert", "drop", "alter", "truncate"]
        for k in forbidden:
            if k in l:
                raise ValueError("unsafe sql")
        if ";" in s:
            raise ValueError("multi statements not allowed")
        if not l.startswith("select") and not l.startswith("explain select"):
            raise ValueError("only select allowed")
        if "limit" not in l:
            s = s + " LIMIT 100"
        return s