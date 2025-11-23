本项目旨在实现一个text2sql工具，并借助微调对电力数据集进行适配

## 前期工作

#实现了一个运行在命令行的简单sql查询程序

简介 | Introduction
- 通过自然语言生成 SQL 并执行查询，支持 Web 与交互式 CLI
- 暂仅支持 MySQL，支持自定义模型调用与 RAG 检索（txt/md/json 等文本）

初次启动配置 | First Run Setup
1) 安装与环境
   - 最低要求：Python 3.11；推荐使用 Conda 管理环境
   - 创建环境：
     - `conda create -y -n text2sql python=3.11`
     - `conda activate text2sql`
   - 安装依赖：
     - `pip install -r requirements.txt`

2) 必需配置
   - 模型：
     - `SILICONFLOW_API_KEY`：API 密钥
     - `MODEL_NAME`：模型名称
     - 可选 `SILICONFLOW_BASE_URL`：默认 `https://api.siliconflow.cn/v1`
   - 数据库（MySQL）：
     - `DB_URL`：如 `mysql://user:pass@host:3306/dbname`
   - 可选：
     - `KB_DIR`：知识库目录路径（用于 RAG，多文件类型）
     - `KB_GLOB`：文件匹配模式，逗号分隔（默认 `*.txt,*.md,*.csv,*.xlsx,*.xls,*.docx`）

3) 快速验证
   - 运行单元测试：`python -m unittest discover -v -s text2sql/tests`
   - 启动 Web：`text2sql\start_web.bat`（后端 8001，前端 8000）
   - 首次连接可用 `-s` 显示并生成 `text2sql/db_info/<db>.json`
   - 保存结果：使用 `-j` 导出 JSON（位于 `text2sql/results/`）

注意事项 | Notes
- `.docx` 已原生支持；`.doc` 解析依赖额外工具，默认不启用，建议转换为 `.docx` 或 `.txt`
- 仅支持单条只读 SELECT 语句，护栏会限制多语句与写操作
- 批量执行可使用 `-import <json文件>`，其格式为问题数组：`[{"question": "..."}, ...]`

开始使用 | Usage
- CLI：`text2sql\start_cli.bat`
- Web：打开浏览器 `http://127.0.0.1:8000`

- 交互命令 | Interactive Commands
  - `-h` 查看帮助
  - `-l N` 设置结果上限
  - `-e` 显示执行计划（MySQL: EXPLAIN）
  - `-d` 干运行（仅显示 SQL）
  - `-j` 保存 JSON（保存三字段：用户问题、生成的sql、查询结果）
  - `-import 路径` 导入 JSON 格式的批量查询，格式参考`./queries/q1.json`
  - `-s` 切换显示数据库表结构（首次连接会生成 `./db_info/<db>.json`）
  - `-showrag` 展示配置的 RAG 知识库信息

- 输出说明 | Output
  - 默认表格输出；选择 `-j` 或 `-c` 将保存到 `./results/`

`.env` 示例 | .env Sample
```bash
# 模型
SILICONFLOW_API_KEY=sk-xxxx
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
MODEL_NAME=YOUR_MODEL_NAME

# 数据库
DB_URL=mysql://user:password@host:3306/db_name

# RAG 知识库
KB_DIR=./rag
KB_GLOB=*.txt,*.md,*.csv,*.xlsx,*.xls,*.docx
```

相关文档 | Docs
- 前端 API 文档：`front_end/API.md`
- 版本变更：`CHANGELOG.md`
版本变更 | Changelog
- 详见 `CHANGELOG.md`