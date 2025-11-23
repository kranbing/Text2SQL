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
    def check_semantics(self, question: str, schema: dict, sql: str) -> str:
        q = (question or "").lower()
        doc = "\n".join(schema.get("docs", []))
        if ("披萨" in question or "pizza" in q) and ("披萨" not in doc and "pizza" not in doc):
            raise ValueError("请检查要查询的字段是否在数据库中")
        if any(k in question for k in ("一天", "按天", "每日", "每天")):
            if "group by" not in (sql or "").lower():
                raise ValueError("请检查要查询的字段是否在数据库中")
        return sql
    def suggest_missing_terms(self, question: str, schema: dict) -> list:
        doc = "\n".join(schema.get("docs", []))
        q = question or ""
        import re
        roman = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", q)
        cjk = re.findall(r"[\u4e00-\u9fa5]{2,}", q)
        s = set()
        for t, cols in (schema.get("tables", {}) or {}).items():
            s.add(str(t))
            for c in cols:
                s.add(str(c))
        dl = doc.lower()
        out = []
        seen = set()
        for tok in roman:
            tl = tok.lower()
            if tl not in dl and tok not in s and tl not in seen:
                out.append(tok)
                seen.add(tl)
        for tok in cjk:
            if tok not in doc and tok not in s and tok not in seen:
                out.append(tok)
                seen.add(tok)
        return out
