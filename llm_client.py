"""
LLM 客户端模块
功能：调用 OpenAI 兼容接口生成 SQL，并支持模型动态切换。
方法：
- generate_sql(question, schema, dialect, limit, context_docs): 返回 SQL 字符串
- reconfigure_model(provider, model_name): 切换模型名
"""
import os
from openai import OpenAI

class LLMClient:
    def __init__(self):
        self._client = None
        self._model_name = os.getenv("MODEL_NAME", None)
        base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
        api_key = os.getenv("SILICONFLOW_API_KEY", "")
        if not api_key:
            raise RuntimeError("未配置 API_KEY")
        if not self._model_name:
            raise RuntimeError("未设置 MODEL_NAME。请选择有效的模型名称。")
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def _extract_sql(self, text: str) -> str:
        t = text.strip()
        if "```" in t:
            t = t.replace("```sql", "").replace("```", "").strip()
        semi = t.find(";")
        if semi != -1:
            t = t[:semi]
        return t.strip()

    def generate_sql(self, question: str, schema: dict, dialect: str, limit: int, context_docs: list[str] | None = None) -> str:
        schema_docs = "\n".join(schema.get("docs", []))[:4000]
        ctx_docs = "\n".join(context_docs or [])[:2000]
        messages = [
            {"role": "system", "content": f"你是一个只返回SQL的助手。目标方言：{dialect}。必须仅返回一条合法的SELECT语句，不要任何解释或代码块；只能使用提供的表与列信息。"},
            {"role": "user", "content": f"问题：{question}\nSchema：\n{schema_docs}\n上下文：\n{ctx_docs}\n输出：一条{dialect}方言的SELECT查询。"},
        ]
        try:
            resp = self._client.chat.completions.create(model=self._model_name, messages=messages, temperature=0)
            text = resp.choices[0].message.content or ""
        except Exception as e:
            msg = str(e)
            if "Model does not exist" in msg or "20012" in msg:
                raise RuntimeError("模型不可用")
            raise
        sql = self._extract_sql(text)
        return sql

    def reconfigure_model(self, provider: str | None = None, model_name: str | None = None):
        if model_name:
            self._model_name = model_name