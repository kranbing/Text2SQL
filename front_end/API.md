# Text2SQL Web API 文档

版本：v0.4.0  
最后更新：2025-11-23  
基本路径：`http://127.0.0.1:8001/v1`  
Content-Type：`application/json`

## 概览
- 覆盖对话生成 SQL、文件上传（批量/知识库）、任务轮询、数据库信息与表结构、知识库展示、下载结果
- 提供 cURL 与前端 `fetch` 示例（调用方式），与 README 对齐

## 对话生成 SQL
- 路径：`POST /chat/completion`
- 请求体：
```json
{
  "message": "查询上季度销售额最高的前 5 名员工",
  "config": {
    "show_schema_insight": true,
    "execute_sql": true,
    "export_json": true,
    "use_rag": true,
    "explain": false
  },
  "limit": 100
}
```
- 典型响应：
```json
{
  "code": 200,
  "status": "success",
  "data": {
    "sql_query": "SELECT ...",
    "query_result": { "columns": ["col"], "rows": [["val"]] },
    "exports": { "json_url": "/v1/downloads/result_20251122_045415.json" }
  }
}
```
- cURL：
```bash
curl -sS -X POST "http://127.0.0.1:8001/v1/chat/completion" \
  -H "Content-Type: application/json" \
  -d '{"message":"近七日订单量","config":{"execute_sql":true,"export_json":true},"limit":100}'
```
- 前端示例：
```js
fetch('http://127.0.0.1:8001/v1/chat/completion', {
  method: 'POST', headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({ message: '近七日订单量', config: { execute_sql: true }, limit: 100 })
}).then(r => r.json());
```

## 扩展：文件上传
- 路径：`POST /tools/upload`（`multipart/form-data`）
- 字段：`file`（上传文件）、`task_type`（`batch_query` 或 `update_kb`）
- 前端示例：
```js
const fd = new FormData();
fd.append('file', file);
fd.append('task_type', 'batch_query');
fetch('http://127.0.0.1:8001/v1/tools/upload', { method: 'POST', body: fd })
  .then(r => r.json());
```
- 响应：
```json
{"code":200,"data":{"task_id":"task_xxx","status":"processing","estimated_time":"30s"}}
```

## 任务状态轮询
- 路径：`GET /tools/task/{task_id}`
- 响应：
```json
{"code":200,"data":{"task_id":"task_xxx","status":"completed","progress":100,"result_url":"/v1/downloads/result_...json"}}
```

## 知识库展示
- 路径：`GET /rag/show`
- 响应：
```json
{"code":200,"data":{"count":1,"files":[{"name":"intro.md","preview":"..."}]}}
```

## 数据库信息与表结构
- 路径：`GET /database/info` → 返回 `dialect/host/database/url`
- 路径：`GET /database/schema` → 返回 `tables:[{table_name, columns:[{name,type,is_primary}]}]`

## 下载结果
- 静态路径：`/v1/downloads/<filename>`（JSON 导出）

## CORS
- 默认允许来源：`http://localhost:8000`、`http://127.0.0.1:8000`

## 错误码
- 400 参数错误；401 未授权；422 生成失败；500 执行错误