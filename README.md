# prompt-rounds

一套用于 AI 编码代理（Claude Code / Codex 等）持续迭代项目的提示词管理工具。

核心思路：把常用的迭代话术拆成独立模块，按需组合成每一轮的提示词文件，一键发给 AI 代理执行，轮次间通过迭代日志传递上下文，实现真正有记忆的连续迭代。

---

## 文件结构

```
prompt-rounds/
├── prompt-library.md     # 所有话术模块的原始文档与使用说明
├── rounds.yaml           # 配置：话术模块内容 + 轮次组合 + 工作区路径 + 执行引擎
├── generate_rounds.py    # 生成轮次文件
├── run_round.py          # 发送轮次给 AI 代理执行
├── result/               # 生成的轮次文件（round_01.md … round_N.md）
├── logs/                 # 每轮执行日志（自动生成，不提交 git）
├── test_rounds.yaml      # 轻量测试配置（验证链路用）
└── result_test/          # 测试轮次生成文件
```

---

## 工作流

```
编辑 rounds.yaml → generate_rounds.py 生成文件 → run_round.py 发给 AI 执行 → logs/ 查看结果
                                                        ↕
                                         docs/iteration-log.md（轮次间记忆）
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

## run_round.py — 发送给 AI 代理执行

支持两个执行引擎，通过 `rounds.yaml` 的 `provider` 字段切换：

| provider | 引擎 | 安装 |
|----------|------|------|
| `codex`（默认） | [OpenAI Codex CLI](https://github.com/openai/codex) | `npm install -g @openai/codex` |
| `claude` | [Claude Code](https://claude.ai/code) | `npm install -g @anthropic-ai/claude-code` |

```bash
# 发送第 1 轮（使用 rounds.yaml 配置的引擎和工作区）
python3 run_round.py --round 1

# 指定工作区（覆盖 yaml 配置）
python3 run_round.py --round 1 --workspace ~/myapp

# 全自动模式（不询问确认）
python3 run_round.py --round 1 --auto

# 多轮依次执行，等上一轮结束再发下一轮
python3 run_round.py --round 1,2,3

# 执行全部轮次
python3 run_round.py --all

# 全自动跑完全部轮次
python3 run_round.py --all --auto

# 不保存日志
python3 run_round.py --round 1 --no-log

# 只预览 prompt，不执行
python3 run_round.py --round 1 --dry-run

# 指定配置文件
python3 run_round.py --round 1 --config my_project.yaml
```

### 注意事项

- 多轮执行时，每轮阻塞等待 AI 完成后再发下一轮
- AI 异常退出（非零退出码）时自动终止，不继续后续轮次
- 中断整个流程请用 `Ctrl+C`
- 每轮结束后会提示 commit + push 工作区改动

### 日志

每轮执行默认自动保存日志到 `logs/`，文件名含轮次编号和时间戳：

```
logs/
├── round_01_20260318_143022.log
├── round_02_20260318_144501.log
└── round_03_20260318_151230.log
```

---

## 轮次间记忆

每轮开始时自动读取工作区 `docs/iteration-log.md`，注入上一轮的改动记录、遗留问题和建议，**优先级高于本轮话术指令**。每轮结束后要求 AI 更新该文件。

首轮或重新开始时可手动写入种子日志：

```bash
# 工作区中创建
vim /path/to/project/docs/iteration-log.md
```

---

## 如何配置 rounds.yaml

```yaml
output_dir: result            # 轮次文件输出目录
file_prefix: round_           # 文件名前缀 → round_01.md
separator: "---"              # 模块间分隔符
provider: codex               # 执行引擎：codex 或 claude
default_workspace: /path/to/project   # AI 工作区默认路径

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

---

## 验证链路

用 `test_rounds.yaml` 跑三轮轻量任务（pwd / git remote / README），验证配置和流程是否正常：

```bash
python3 run_round.py --all --auto --config test_rounds.yaml
```

---

## 复用到新项目

复制一份 `rounds.yaml`，修改 `sections`、`rounds`、`provider` 和 `default_workspace`，脚本不用改：

```bash
python3 generate_rounds.py new_project.yaml
python3 run_round.py --all --auto --config new_project.yaml
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
| 路由与用户旅程专项话术 | 5条核心旅程路由架构审查 |
| 输出格式约束话术 | 约束 AI 的输出结构 |

---

## 依赖

- Python 3.9+
- `pyyaml`（首次运行自动安装）
- `@openai/codex` 或 Claude Code（取决于 `provider` 配置）

---

## License

[MIT](./LICENSE) © [whyy9527](https://github.com/whyy9527)

可自由使用、修改和分发，但须保留原作者署名及指向本仓库的来源链接。
