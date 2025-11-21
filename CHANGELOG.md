## 0.2.0
- Add JSON import with validation & normalization
- Add error logging to import_errors.jsonl
- Interactive CLI commands: :model, :import-json
- Switch LLM client to standard OpenAI API for SiliconFlow
- Add tests and coverage reporting
- Update README with bilingual instructions

## 0.1.0
- Initial CLI, SQLite sample DB, basic orchestration
## 0.2.1
- Temporarily disable JSON import (`-imptjson`) and keep placeholder
- Add model call spinner during SQL generation
- Save JSON/CSV with fields: 用户问题, 生成的sql, 查询结果
- Improve CLI startup: show DB connect spinner and status