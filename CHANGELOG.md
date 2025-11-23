## 0.1.0
- 初始 CLI、SQLite 示例数据库、基础编排功能

## 0.3.0
- 新增带验证和规范化的 JSON 导入功能
- 添加错误日志记录至 import_errors.jsonl 文件
- 交互式 CLI 命令：:model, :import-json
- 暂时使用OpenAI API（用于 SiliconFlow）调用 LLM 客户端 
- 添加测试和覆盖率报告
- 更新 README，包含双语使用说明

## 0.3.1
- 暂时禁用 JSON 导入功能，保留占位符
- 在 SQL 生成期间添加模型调用旋转提示符
- 保存包含字段的 JSON/CSV 文件：用户问题、生成的 SQL、查询结果
- 改进 CLI 启动：显示数据库连接旋转提示符和状态信息

## 0.3.2
- 统一数据库方言为 MySQL，删除 MSSQL 相关分支与说明
- 扩展 RAG 知识库文件类型：支持 txt/md/csv/xlsx/xls/docx；在编排中通过 `KB_DIR`/`KB_GLOB` 自动加载
- 批量执行增强：单条异常不再中断整次批量；新增批量导出 JSON/CSV；所有 JSON 输出采用缩进与行尾换行，提升可读性
- README 整理：新增“初次启动配置”步骤，涵盖 Conda 环境、依赖安装、必需环境变量与 RAG 可选配置；命令路径统一为 `python text2sql/cli.py`
- 依赖管理：生成 `requirements.txt` 并提供 Conda 环境创建与安装指引
- 细节优化：`db_info` 与结果 JSON 文件均为缩进+换行格式；保持单语句只读与 LIMIT 护栏
- 测试：现有单元测试通过（Schema Provider），与上述改动兼容