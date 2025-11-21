"""
CLI 交互模块
功能：提供 REPL 风格交互，支持模型切换、结果格式、导入、显示 Schema。
方法：
- main(): 启动交互界面
"""
import argparse
import os
import sys
import time
import threading
from orchestrator import Orchestrator

def _load_env_file():
    base = os.path.dirname(__file__)
    env_path = os.path.join(base, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith("#"):
                        continue
                    if "=" in s:
                        k, v = s.split("=", 1)
                        k = k.strip()
                        v = v.strip()
                        if k and v and (os.getenv(k) is None):
                            os.environ[k] = v
        except Exception:
            pass

def main():
    _load_env_file()
    parser = argparse.ArgumentParser(description="Text2SQL CLI（交互模式）。启动后直接输入问题。输入 ':h' 查看交互帮助。")
    parser.add_argument("--limit", dest="limit", type=int, default=100)
    parser.add_argument("--explain", dest="explain", action="store_true")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true")
    parser.add_argument("--json", dest="json", action="store_true")
    parser.add_argument("--csv", dest="csv", action="store_true")
    parser.add_argument("--show-schema", dest="show_schema", action="store_true")
    args = parser.parse_args()
    orchestrator = Orchestrator()
    stop_evt = threading.Event()
    def _spin():
        frames = "|/-\\"
        i = 0
        while not stop_evt.is_set():
            sys.stdout.write("\r正在连接数据库 " + frames[i % len(frames)])
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        sys.stdout.write("\r")
        sys.stdout.flush()
    t = threading.Thread(target=_spin, daemon=True)
    t.start()
    try:
        db_url = orchestrator.db_url
        if not db_url:
            raise RuntimeError("Missing DB_URL. Please set MySQL/SQL Server connection string")
        dialect = "mssql" if db_url.startswith("mssql://") else "mysql"
        orchestrator.schema.load(db_url, dialect)
        stop_evt.set()
        t.join()
        print("数据库连接成功")
    except Exception as e:
        stop_evt.set()
        t.join()
        print(f"数据库连接失败: {e}")
        return
    print("输入 '-h' 查看帮助，'exit' 退出")
    limit = args.limit
    explain = args.explain
    dry_run = args.dry_run
    as_json = args.json
    as_csv = args.csv
    show_schema = args.show_schema
    while True:
        try:
            q = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            continue

        if q.lower() in ("exit", "quit"): 
            break

        if q.lower() in ("-h", "-help", "--h", "--help"):
            print("命令：\n  输入问题执行查询\n  -h 显示帮助\n  -e 切换是否显示执行计划\n  -d 切换干运行（仅显示SQL不执行）\n  -j 切换JSON输出\n  -c 切换CSV输出\n  -l N 设置LIMIT 上限\n  -imptjson 路径（暂不可用）\n  -s 切换显示数据库表结构\n  exit 退出")
            continue

        if q.lower().startswith("-imptjson"):
            parts = q.split(maxsplit=1)
            if len(parts) == 2 and parts[1].strip():
                path = parts[1].strip()
                try:
                    if not orchestrator.db_url:
                        print("未配置 DB_URL（MySQL）。请设置环境变量后再导入")
                        continue
                    res = orchestrator.schema.import_json(path, orchestrator.db_url, orchestrator.dialect)
                    if res.get("errors"):
                        print(f"导入完成，有错误 {len(res['errors'])} 条，详见 import_errors.jsonl")
                    else:
                        print("导入成功")
                except Exception as e:
                    print(f"导入失败: {e}")
            else:
                print("用法：-imptjson <filepath>")
            continue

        if q.lower().startswith("-l"):
            parts = q.split()
            if len(parts) == 2 and parts[1].isdigit():
                limit = int(parts[1])
                print(f"LIMIT={limit}")
            else:
                print("用法：-l 100")
            continue

        if q.lower() == "-e":
            explain = not explain
            print(f"EXPLAIN={'ON' if explain else 'OFF'}")
            continue

        if q.lower() == "-d":
            dry_run = not dry_run
            print(f"DRY_RUN={'ON' if dry_run else 'OFF'}")
            continue

        if q.lower() == "-j":
            as_json = not as_json
            if as_json:
                as_csv = False
            print(f"JSON={'ON' if as_json else 'OFF'}")
            continue

        if q.lower() == "-c":
            as_csv = not as_csv
            if as_csv:
                as_json = False
            print(f"CSV={'ON' if as_csv else 'OFF'}")
            continue

        if q.lower() == "-s":
            show_schema = not show_schema
            print(f"SCHEMA={'ON' if show_schema else 'OFF'}")
            continue

        orchestrator.run(
            question=q,
            limit=limit,
            explain=explain,
            dry_run=dry_run,
            as_json=as_json,
            as_csv=as_csv,
            show_schema=show_schema,
        )

if __name__ == "__main__":
    main()