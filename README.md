# prompt-rounds

一套用于 AI 编码代理（Claude Code / Codex / Cursor Agent 等）持续迭代项目的提示词管理工具。

核心思路：把常用的迭代话术拆成独立模块，按需组合成每一轮的提示词文件，一键发给 AI 代理执行。

---

## 文件结构

```
prompt-rounds/
├── prompt-library.md     # 所有话术模块的原始文档与使用说明
├── rounds.yaml           # 配置：话术模块内容 + 轮次组合 + 工作区路径
├── generate_rounds.py    # 生成轮次文件
├── run_round.py          # 发送轮次给 codex exec 执行
├── result/               # 生成的轮次文件（round_01.md … round_N.md）
└── logs/                 # 每轮执行日志（自动生成，不提交 git）
```

---

## 工作流

```
编辑 rounds.yaml → generate_rounds.py 生成文件 → run_round.py 发给 codex 执行 → logs/ 查看结果
```

---

## generate_rounds.py — 生成轮次文件

```bash
# 生成全部轮次文件
python3 generate_rounds.py

# 列出所有轮次定义（不生成文件）
python3 generate_rounds.py --list

# 只生成指定轮次
python3 generate_rounds.py --round 3
python3 generate_rounds.py --round 1,5,12

# 指定配置文件 / 覆盖输出目录
python3 generate_rounds.py my_project.yaml
python3 generate_rounds.py -o ./output
```

生成的文件只包含话术正文，无标题无标签，可直接粘贴或由 `run_round.py` 发出。

---

## run_round.py — 发送给 codex exec

依赖：[Codex CLI](https://github.com/openai/codex) (`npm install -g @openai/codex`)

```bash
# 发送第 1 轮（使用 rounds.yaml 里配置的默认工作区）
python3 run_round.py --round 1

# 指定工作区（覆盖 yaml 配置）
python3 run_round.py --round 1 --workspace ~/myapp

# 全自动模式（codex 不询问确认）
python3 run_round.py --round 1 --auto

# 多轮依次执行，等上一轮结束再发下一轮
python3 run_round.py --round 1,2,3

# 执行 yaml 中定义的全部轮次
python3 run_round.py --all

# 全自动跑完全部轮次
python3 run_round.py --all --auto

# 不保存日志
python3 run_round.py --round 1 --no-log

# 验证工作区配置（pwd / ls / README，不调用 codex）
python3 run_round.py --round 1 --test

# 只预览 prompt，不执行
python3 run_round.py --round 1 --dry-run

# 指定配置文件
python3 run_round.py --round 1 --config my_project.yaml
```

### 日志

每轮执行默认自动保存日志到 `logs/`，文件名含轮次编号和时间戳：

```
logs/
├── round_01_20260318_143022.log
├── round_02_20260318_144501.log
└── round_03_20260318_151230.log
```

每个日志文件开头包含元信息（时间、工作区、话术文件），后面是 codex 的完整输出。

---

## 如何配置 rounds.yaml

```yaml
output_dir: result            # 轮次文件输出目录
file_prefix: round_           # 文件名前缀 → round_01.md
separator: "---"              # 模块间分隔符
default_workspace: /path/to/project   # codex 工作区默认路径

sections:
  总控话术: |
    你的话术内容……

  产品质感专项话术: |
    你的话术内容……

rounds:
  - num: 1
    combo: [总控话术, 产品质感专项话术]
  - num: 2
    combo: [总控话术]
```

- `sections`：可复用的话术模块，key 是名称，value 是正文
- `rounds`：每轮使用哪些模块，按顺序拼合
- `default_workspace`：`run_round.py` 的默认工作区，可被 `--workspace` 覆盖

---

## 复用到新项目

复制一份 `rounds.yaml`，修改 `sections`、`rounds` 和 `default_workspace`，脚本不用改：

```bash
python3 generate_rounds.py new_project.yaml
python3 run_round.py --round 1 --config new_project.yaml
```

---

## 内置话术模块

当前 `rounds.yaml` 预置了以下模块，适用于小程序 + 管理后台类项目：

| 模块名 | 用途 |
|--------|------|
| 总控话术 | 每轮必带的基础迭代指令 |
| 小程序前台专项话术 | 聚焦前台用户体验与业务承接 |
| 管理后台专项话术 | 聚焦后台操作效率与业务逻辑 |
| 前后台一致性专项话术 | 修复前后台割裂问题 |
| 产品质感专项话术 | 视觉层级、留白、品牌感 |
| 易用性专项话术 | 消除操作摩擦，提升流程完成率 |
| 业务闭环专项话术 | 强化核心转化路径 |
| 工程质量专项话术 | 组件拆分、命名、可维护性 |
| 输出格式约束话术 | 约束 AI 的输出结构 |

---

## 依赖

- Python 3.9+
- `pyyaml`（首次运行自动安装）
- `@openai/codex`（仅 `run_round.py` 需要）

---

## License

[MIT](./LICENSE) © [whyy9527](https://github.com/whyy9527)

可自由使用、修改和分发，但须保留原作者署名及指向本仓库的来源链接。
