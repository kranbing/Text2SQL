"""
RAG 检索模块
功能：构建向量索引或启用简易检索，返回相关文档。
方法：
- RAGIndex.build(docs): 构建索引
- RAGRetriever.set_index(index): 设置索引
- RAGRetriever.query(question, top_k): 返回相关文档列表
"""
class RAGIndex:
    def __init__(self):
        self.docs = []
        self.vs = None
        try:
            from langchain_openai import OpenAIEmbeddings
            from langchain_community.vectorstores import FAISS
            self._emb_cls = OpenAIEmbeddings
            self._vs_cls = FAISS
        except Exception:
            self._emb_cls = None
            self._vs_cls = None
    def build(self, docs: list[str]):
        self.docs = docs or []
        if self._emb_cls and self._vs_cls and self.docs:
            try:
                import os
                base_url = os.getenv("SILICONFLOW_BASE_URL", None)
                api_key = os.getenv("SILICONFLOW_API_KEY", None)
                kwargs = {}
                if base_url:
                    kwargs["base_url"] = base_url
                if api_key:
                    kwargs["api_key"] = api_key
                emb = self._emb_cls(**kwargs)
                self.vs = self._vs_cls.from_texts(self.docs, emb)
            except Exception:
                self.vs = None

class RAGRetriever:
    def __init__(self):
        self.index = None
    def set_index(self, index: RAGIndex):
        self.index = index
    def query(self, question: str, top_k: int = 5) -> list[str]:
        if not self.index:
            return []
        if self.index.vs is not None:
            try:
                docs = self.index.vs.similarity_search(question, k=top_k)
                return [d.page_content for d in docs]
            except Exception:
                pass
        q = question.lower()
        scored = []
        for d in self.index.docs:
            s = 0
            for tok in q.split():
                if tok and tok in d.lower():
                    s += 1
            scored.append((s, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for s, d in scored[:top_k] if s > 0]