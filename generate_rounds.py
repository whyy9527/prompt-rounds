#!/usr/bin/env python3
"""
generate_rounds.py — 从 YAML 配置生成迭代轮次 Markdown 文件

用法：
  python generate_rounds.py                  # 使用同目录下 rounds.yaml
  python generate_rounds.py my_config.yaml   # 指定配置文件
  python generate_rounds.py -o output_dir    # 覆盖输出目录
  python generate_rounds.py --list           # 只列出轮次，不生成文件
  python generate_rounds.py --round 3        # 只生成第 3 轮
  python generate_rounds.py --round 1,5,12   # 只生成指定几轮
"""

import sys
import os
import argparse

try:
    import yaml
except ImportError:
    print("缺少 pyyaml，正在安装...")
    os.system(f"{sys.executable} -m pip install pyyaml -q")
    import yaml


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_round_content(num: int, combo: list[str], sections: dict, separator: str) -> str:
    parts = []
    for name in combo:
        if name not in sections:
            print(f"  [警告] 第{num}轮引用了未定义的模块：'{name}'，已跳过")
            continue
        parts.append(sections[name].rstrip())
    sep = f"\n\n{separator}\n\n"
    return sep.join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description="生成迭代轮次 Markdown 文件")
    parser.add_argument("config", nargs="?", default=None, help="YAML 配置文件路径")
    parser.add_argument("-o", "--output", default=None, help="覆盖输出目录")
    parser.add_argument("--list", action="store_true", help="只列出轮次定义，不生成文件")
    parser.add_argument("--round", default=None, help="只生成指定轮次，如 3 或 1,5,12")
    args = parser.parse_args()

    # 找配置文件
    if args.config:
        config_path = args.config
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "rounds.yaml")

    if not os.path.exists(config_path):
        print(f"找不到配置文件：{config_path}")
        sys.exit(1)

    config = load_config(config_path)
    sections = config.get("sections", {})
    rounds = config.get("rounds", [])
    separator = config.get("separator", "---")
    file_prefix = config.get("file_prefix", "round_")

    # 输出目录
    if args.output:
        output_dir = args.output
    else:
        config_dir = os.path.dirname(os.path.abspath(config_path))
        output_dir = os.path.join(config_dir, config.get("output_dir", "result"))

    # 过滤轮次
    if args.round:
        target_nums = set(int(x.strip()) for x in args.round.split(","))
        rounds = [r for r in rounds if r["num"] in target_nums]

    # --list 模式
    if args.list:
        print(f"\n共 {len(config.get('rounds', []))} 轮，已加载模块：{list(sections.keys())}\n")
        for r in config.get("rounds", []):
            combo_str = " + ".join(r["combo"])
            print(f"  第{r['num']:>2}轮：{combo_str}")
        return

    # 生成文件
    os.makedirs(output_dir, exist_ok=True)
    generated = []

    for r in rounds:
        num = r["num"]
        combo = r["combo"]
        content = build_round_content(num, combo, sections, separator)
        filename = f"{file_prefix}{num:02d}.md"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        generated.append((num, filename, combo))
        print(f"  [生成] {filename}  ←  {' + '.join(combo)}")

    print(f"\n完成：共生成 {len(generated)} 个文件 → {output_dir}/")


if __name__ == "__main__":
    main()
