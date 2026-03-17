#!/usr/bin/env python3
"""
run_round.py — 把轮次文件发给 codex exec 执行

用法：
  python3 run_round.py --round 1                        # 用 rounds.yaml 里配置的默认工作区
  python3 run_round.py --round 1 --workspace ~/myapp    # 指定工作区
  python3 run_round.py --round 1 --auto                 # 全自动模式（--full-auto）
  python3 run_round.py --round 1 --dry-run              # 只打印命令，不执行
  python3 run_round.py --round 1,3,7                    # 依次执行多轮
  python3 run_round.py --round 1 --config other.yaml    # 指定配置文件
"""

import sys
import os
import subprocess
import argparse

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


def run_round(num: int, config: dict, config_dir: str, workspace, auto: bool, dry_run: bool):
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

    subprocess.run(cmd, input=prompt, text=True)


def main():
    parser = argparse.ArgumentParser(description="把轮次文件发给 codex exec 执行")
    parser.add_argument("--round", required=True, help="轮次编号，如 1 或 1,3,7")
    parser.add_argument("--workspace", default=None, help="codex 工作区路径（覆盖 yaml 配置）")
    parser.add_argument("--config", default=None, help="指定 rounds.yaml 路径")
    parser.add_argument("--auto", action="store_true", help="全自动模式（--full-auto，无需人工确认）")
    parser.add_argument("--dry-run", action="store_true", help="只打印命令和 prompt 预览，不实际执行")
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

    if not args.dry_run:
        find_codex()

    nums = [int(x.strip()) for x in args.round.split(",")]
    for num in nums:
        run_round(num, config, config_dir, args.workspace, args.auto, args.dry_run)


if __name__ == "__main__":
    main()
