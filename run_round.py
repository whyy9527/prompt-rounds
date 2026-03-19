#!/usr/bin/env python3
"""
run_round.py — 把轮次文件发给 codex exec 执行

用法：
  python3 run_round.py --round 1                        # 用 rounds.yaml 里配置的默认工作区
  python3 run_round.py --round 1 --workspace ~/myapp    # 指定工作区
  python3 run_round.py --round 1 --auto                 # 全自动模式（--full-auto）
  python3 run_round.py --round 1 --dry-run              # 只打印命令，不执行
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


ITERATION_LOG = "docs/iteration-log.md"

CONTEXT_PREFIX = """【迭代上下文 — 最高优先级】
以下是上一轮留下的建议和遗留问题。本轮必须优先处理，这比本轮话术本身的指令优先级更高。
如果上一轮建议与本轮话术方向有冲突，以上一轮建议为准。
不要跳过，不要重新从头分析，直接承接上一轮的结论继续推进。

{log_content}

【本轮话术指令（在完成上述建议后执行）】
"""

CONTEXT_PREFIX_FIRST = """【迭代上下文】
这是第一轮，工作区中尚无迭代记录。

【本轮任务】
"""

CONTEXT_SUFFIX = """

---
【迭代日志更新】
本轮结束后，请将工作区中的 `{log_path}` 更新为以下格式（覆盖写入）：

# 迭代日志（第{num}轮）

## 本轮改动
- 简要列出本轮修改了什么（3-5条）

## 遗留问题
- 本轮发现但未处理的问题（不超过3条）

## 下一轮建议
- 下一轮最该优先做的3件事（具体、可操作）

这个文件是轮次间传递上下文的唯一渠道，请务必更新。
"""


def build_prompt(num: int, base_prompt: str, cwd: str) -> str:
    log_path = os.path.join(cwd, ITERATION_LOG)
    suffix = CONTEXT_SUFFIX.format(log_path=ITERATION_LOG, num=num)

    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as f:
            log_content = f.read().strip()
        prefix = CONTEXT_PREFIX.format(log_path=ITERATION_LOG, log_content=log_content)
        print(f"[第{num}轮] 已注入上一轮迭代日志（{len(log_content)} 字符）")
    else:
        prefix = CONTEXT_PREFIX_FIRST
        print(f"[第{num}轮] 首轮，无历史迭代日志")

    return prefix + base_prompt + suffix


def run_round(num: int, config: dict, config_dir: str, workspace, auto: bool, dry_run: bool, no_log: bool = False):
    prefix = config.get("file_prefix", "round_")
    output_dir = os.path.join(config_dir, config.get("output_dir", "result"))
    round_file = os.path.join(output_dir, f"{prefix}{num:02d}.md")

    if not os.path.exists(round_file):
        print(f"[错误] 找不到文件：{round_file}，请先运行 generate_rounds.py")
        return

    with open(round_file, encoding="utf-8") as f:
        base_prompt = f.read().strip()

    # 工作区：参数 > yaml > 当前目录
    cwd = workspace or config.get("default_workspace") or os.getcwd()
    cwd = os.path.expanduser(cwd)

    if not os.path.isdir(cwd):
        print(f"[错误] 工作区目录不存在：{cwd}")
        return

    prompt = build_prompt(num, base_prompt, cwd)

    cmd = ["codex", "exec", "-C", cwd, "-c", 'model_reasoning_effort="medium"']
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

    if no_log:
        proc = subprocess.run(cmd, input=prompt, text=True)
        returncode = proc.returncode
    else:
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
        returncode = proc.returncode

    if returncode != 0:
        print(f"[第{num}轮] codex 异常退出（code {returncode}），已终止后续轮次")
        sys.exit(returncode)

    print(f"\n{'=' * 40}")
    print(f"[第{num}轮完成] 请及时 commit + push 工作区改动：")
    print(f"  cd {cwd}")
    print(f"  git add -A && git commit -m 'round {num}: <简述改动>' && git push")
    print(f"{'=' * 40}\n")


def main():
    parser = argparse.ArgumentParser(description="把轮次文件发给 codex exec 执行")
    parser.add_argument("--round", default=None, help="轮次编号，如 1 或 1,3,7")
    parser.add_argument("--all", action="store_true", help="依次执行 yaml 中定义的全部轮次")
    parser.add_argument("--workspace", default=None, help="codex 工作区路径（覆盖 yaml 配置）")
    parser.add_argument("--config", default=None, help="指定配置文件路径")
    parser.add_argument("--auto", action="store_true", help="全自动模式（--full-auto，无需人工确认）")
    parser.add_argument("--dry-run", action="store_true", help="只打印命令和 prompt 预览，不实际执行")
    parser.add_argument("--no-log", action="store_true", help="不保存日志")
    args = parser.parse_args()

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

    if args.all:
        nums = [r["num"] for r in config.get("rounds", [])]
    elif args.round:
        nums = [int(x.strip()) for x in args.round.split(",")]
    else:
        parser.error("请指定 --round 或 --all")

    for num in nums:
        run_round(num, config, config_dir, args.workspace, args.auto, args.dry_run, args.no_log)


if __name__ == "__main__":
    main()
