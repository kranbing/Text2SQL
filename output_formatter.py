# 输出与结果保存模块
# 功能：格式化查询结果为表格、JSON、CSV，并保存到 results 目录。
# 方法：
# - to_table(rows, headers): 返回表格字符串
# - to_json(rows, headers): 返回JSON字符串
# - to_csv(rows, headers): 返回CSV字符串
# - save_json(rows, headers, filename=None): 保存JSON文件并返回路径
# - save_csv(rows, headers, filename=None): 保存CSV文件并返回路径
import json
import io
import csv
import os
from datetime import datetime

class OutputFormatter:
    def to_table(self, rows, headers) -> str:
        widths = [len(h) for h in headers]
        for r in rows:
            for i, h in enumerate(headers):
                try:
                    v = str(r[h])
                except Exception:
                    v = str(r[i])
                if len(v) > widths[i]:
                    widths[i] = len(v)
        line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
        sep = "-+-".join("-" * w for w in widths)
        out = [line, sep]
        for r in rows:
            line_vals = []
            for i, h in enumerate(headers):
                try:
                    v = str(r[h])
                except Exception:
                    v = str(r[i])
                line_vals.append(v.ljust(widths[i]))
            out.append(" | ".join(line_vals))
        return "\n".join(out)
    def to_json(self, rows, headers) -> str:
        out = []
        for r in rows:
            item = {}
            for i, h in enumerate(headers):
                try:
                    item[h] = r[h]
                except Exception:
                    item[h] = r[i]
            out.append(item)
        return json.dumps(out, ensure_ascii=False)
    def to_csv(self, rows, headers) -> str:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(headers)
        for r in rows:
            row_vals = []
            for i, h in enumerate(headers):
                try:
                    row_vals.append(r[h])
                except Exception:
                    row_vals.append(r[i])
            w.writerow(row_vals)
        return buf.getvalue()
    def save_json(self, question: str, sql: str, rows, headers, filename: str | None = None) -> str:
        base = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(base, exist_ok=True)
        name = filename or f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = os.path.join(base, name)
        result_rows = []
        for r in rows:
            item = {}
            for i, h in enumerate(headers):
                try:
                    item[h] = r[h]
                except Exception:
                    item[h] = r[i]
            result_rows.append(item)
        payload = {"用户问题": question, "SQL查询语句": sql, "查询结果": result_rows}
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False))
        return path
    def save_csv(self, question: str, sql: str, rows, headers, filename: str | None = None) -> str:
        base = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(base, exist_ok=True)
        name = filename or f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path = os.path.join(base, name)
        result_rows = []
        for r in rows:
            item = {}
            for i, h in enumerate(headers):
                try:
                    item[h] = r[h]
                except Exception:
                    item[h] = r[i]
            result_rows.append(item)
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["用户问题", "SQL查询语句", "查询结果"])
            w.writerow([question, sql, json.dumps(result_rows, ensure_ascii=False)])
        return path