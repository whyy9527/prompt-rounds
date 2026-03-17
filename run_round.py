#!/usr/bin/env python3
"""
run_round.py — 把轮次文件发给 codex exec 执行

用法：
  python3 run_round.py --round 1                        # 用 rounds.yaml 里配置的默认工作区
  python3 run_round.py --round 1 --workspace ~/myapp    # 指定工作区
  python3 run_round.py --round 1 --auto                 # 全自动模式（--full-auto）
  python3 run_round.py --round 1 --dry-run              # 只打印命令，不执行
  python3 run_round.py --round 1 --test                 # 用轻量命令验证工作区（不调用 codex）
  python3 run_round.py --round 1,3,7                    # 依次执行多轮
  python3 run_round.py --round 1 --no-log               # 不保存日志
  python3 run_round.py --all                            # 依次执行全部轮次
  python3 run_round.py --round 1 --config other.yaml    # 指定配置文件
"""

import sys
import os
import subprocess
import argparse
from datetime import datetime

try:
    import yaml
except ImportError:
    os.system(f"{sys.executable} -m pip install pyyaml -q")
    import yaml


def find_codex() -> str:
    result = subprocess.run(["which", "codex"], capture_output=True, text=True)
    if result.returncode != 0:
        print("找不到 codex，请先安装：npm install -g @openai/codex")
        sys.exit(1)
    return result.stdout.strip()


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run_round(num: int, config: dict, config_dir: str, workspace, auto: bool, dry_run: bool, test: bool = False, no_log: bool = False):
    prefix = config.get("file_prefix", "round_")
    output_dir = os.path.join(config_dir, config.get("output_dir", "result"))
    round_file = os.path.join(output_dir, f"{prefix}{num:02d}.md")

    if not os.path.exists(round_file):
        print(f"[错误] 找不到文件：{round_file}，请先运行 generate_rounds.py")
        return

    with open(round_file, encoding="utf-8") as f:
        prompt = f.read().strip()

    # 工作区：参数 > yaml > 当前目录
    cwd = workspace or config.get("default_workspace") or os.getcwd()
    cwd = os.path.expanduser(cwd)

    if not os.path.isdir(cwd):
        print(f"[错误] 工作区目录不存在：{cwd}")
        return

    # 构造 codex 命令
    # 用 stdin 传 prompt（避免 shell 转义问题）
    cmd = ["codex", "exec", "-C", cwd]
    if auto:
        cmd.append("--full-auto")
    cmd.append("-")  # 从 stdin 读取 prompt

    print(f"\n[第{num}轮] 工作区：{cwd}")
    print(f"[第{num}轮] 话术文件：{round_file}")
    print(f"[第{num}轮] 命令：{' '.join(cmd)}\n")

    if dry_run:
        print("--- prompt 预览 ---")
        print(prompt[:300] + ("..." if len(prompt) > 300 else ""))
        print("--- dry-run，未执行 ---\n")
        return

    if test:
        print("--- [test 模式] 验证工作区，不调用 codex ---")
        subprocess.run(["pwd"], cwd=cwd)
        subprocess.run(["ls", "-1"], cwd=cwd)
        readme = os.path.join(cwd, "README.md")
        if os.path.exists(readme):
            print("\n--- README.md 前 10 行 ---")
            subprocess.run(["head", "-10", "README.md"], cwd=cwd)
        print(f"\n--- prompt 将发送 {len(prompt)} 字符 ---\n")
        return

    if no_log:
        subprocess.run(cmd, input=prompt, text=True)
        return

    # 日志文件：logs/round_01_20260318_143022.log
    log_dir = os.path.join(config_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"round_{num:02d}_{timestamp}.log")

    header = (
        f"=== 第{num}轮 ===\n"
        f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"工作区：{cwd}\n"
        f"话术文件：{round_file}\n"
        f"{'=' * 40}\n\n"
    )

    print(f"[第{num}轮] 日志：{log_file}")

    with open(log_file, "w", encoding="utf-8") as log:
        log.write(header)
        log.flush()

        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True
        )
        proc.stdin.write(prompt)
        proc.stdin.close()

        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            log.write(line)
            log.flush()

        proc.wait()

    print(f"\n[第{num}轮] 日志已保存：{log_file}")


def main():
    parser = argparse.ArgumentParser(description="把轮次文件发给 codex exec 执行")
    parser.add_argument("--round", default=None, help="轮次编号，如 1 或 1,3,7")
    parser.add_argument("--all", action="store_true", help="依次执行 yaml 中定义的全部轮次")
    parser.add_argument("--workspace", default=None, help="codex 工作区路径（覆盖 yaml 配置）")
    parser.add_argument("--config", default=None, help="指定 rounds.yaml 路径")
    parser.add_argument("--auto", action="store_true", help="全自动模式（--full-auto，无需人工确认）")
    parser.add_argument("--dry-run", action="store_true", help="只打印命令和 prompt 预览，不实际执行")
    parser.add_argument("--test", action="store_true", help="用轻量命令验证工作区（pwd / ls / README），不调用 codex")
    parser.add_argument("--no-log", action="store_true", help="不保存日志")
    args = parser.parse_args()

    # 找配置文件
    if args.config:
        config_path = os.path.abspath(args.config)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "rounds.yaml")

    if not os.path.exists(config_path):
        print(f"找不到配置文件：{config_path}")
        sys.exit(1)

    config = load_config(config_path)
    config_dir = os.path.dirname(config_path)

    if not args.dry_run and not args.test:
        find_codex()

    if args.all:
        nums = [r["num"] for r in config.get("rounds", [])]
    elif args.round:
        nums = [int(x.strip()) for x in args.round.split(",")]
    else:
        parser.error("请指定 --round 或 --all")

    for num in nums:
        run_round(num, config, config_dir, args.workspace, args.auto, args.dry_run, args.test, args.no_log)


if __name__ == "__main__":
    main()
