本文实现了一个text2sql项目，旨在对电力数据集进行lora微调，项目总体基于huggingface、langchain和db-gpt-hub搭建

# 前期工作

Text2SQL 项目（CLI）

简介 | Introduction
- 通过自然语言生成 SQL 并执行查询，支持交互式 CLI 模式
- 支持 MySQL/SQL Server，支持基于硅基流动的模型调用与 RAG 检索

环境变量配置 | Environment Variables
- 数据库 | Database
  - `DB_URL`：如 `mysql://user:pass@host:3306/dbname` 或 `mssql://user:pass@host:1433/dbname?driver=ODBC+Driver+17+for+SQL+Server`
  - `DIALECT`：自动根据 `DB_URL` 选择，无需设置
- 模型 | Model
  - `SILICONFLOW_API_KEY`：硅基流动 API 密钥
  - `SILICONFLOW_BASE_URL`：默认 `https://api.siliconflow.cn/v1`
  - `MODEL_NAME`：模型名称（在硅基流动控制台可用的 ID）
  - 可选：`OPENAI_BASE_URL` / `OPENAI_API_KEY`（如改用 OpenAI 兼容端点）
- 其他 | Others
  - 可使用 `.env` 或系统环境变量注入；不建议将密钥写入代码或日志

数据库导入 | Database Import
- 当前状态：`-imptjson` 功能暂不可用（占位）。
- 计划：恢复后支持 JSON 校验、规范化和错误记录，兼容 MySQL/SQL Server。

命令行用法 | CLI Usage
- 交互命令 | Interactive Commands
  - `-h` 查看帮助
  - `-l N` 设置结果上限
  - `-e` 切换执行计划（MySQL: EXPLAIN；SQL Server: SHOWPLAN_TEXT）
  - `-d` 干运行（仅显示 SQL）
  - `-j` 保存 JSON；`-c` 保存 CSV（保存三字段：用户问题、生成的sql、查询结果）
  - `-imptjson 路径` 导入 JSON（暂不可用）
  - `-s` 切换显示数据库表结构（首次连接会生成 `text2sql/db_info/<db>.json`）
- 典型场景 | Examples
  - 查询示例：`最近30天新增用户按天统计`
  - 保存 JSON/CSV：使用 `-j` 或 `-c`
- 输出说明 | Output
  - 默认表格输出；选择 `-j` 或 `-c` 将保存到 `text2sql/results/`
  - CSV 三列：用户问题、生成的sql、查询结果（结果集为 JSON 字符串）

示例配置 | Example Config
- `.env.example`（需自行复制为 `.env` 并填充）：
  - `DB_URL= mysql://user:pass@host:3306/db`
  - `DIALECT= mysql`
  - `SILICONFLOW_API_KEY= sk-xxxx`
  - `SILICONFLOW_BASE_URL= https://api.siliconflow.cn/v1`
  - `MODEL_NAME= Qwen/Qwen3-Next-80B-A3B-Instruct`

版本变更 | Changelog
- 请查看 `CHANGELOG.md`