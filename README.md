# prompt-rounds

一套用于 AI 编码代理（Claude Code / Codex / Cursor Agent 等）持续迭代项目的提示词管理工具。

核心思路：把常用的迭代话术拆成独立模块，按需组合成每一轮的提示词文件，直接粘贴给 AI 代理使用。

---

## 文件结构

```
prompt-rounds/
├── prompt-library.md     # 所有话术模块的原始文档与使用说明
├── rounds.yaml           # 配置：定义话术模块内容 + 每轮的组合方式
├── generate_rounds.py    # 生成脚本
└── result/               # 生成的轮次文件（round_01.md … round_N.md）
```

---

## 快速开始

```bash
# 生成全部轮次文件
python3 generate_rounds.py

# 列出所有轮次定义（不生成文件）
python3 generate_rounds.py --list

# 只生成第 3 轮
python3 generate_rounds.py --round 3

# 只生成第 1、5、12 轮
python3 generate_rounds.py --round 1,5,12

# 指定配置文件
python3 generate_rounds.py my_project.yaml

# 覆盖输出目录
python3 generate_rounds.py -o ./output
```

依赖：`pyyaml`（首次运行自动安装）

---

## 如何配置

编辑 `rounds.yaml`：

```yaml
output_dir: result       # 输出目录
file_prefix: round_      # 文件名前缀，生成 round_01.md、round_02.md…
separator: "---"         # 模块之间的分隔符

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

- `sections`：定义所有可复用的话术模块，key 是名称，value 是正文
- `rounds`：定义每轮使用哪些模块，按顺序拼合，模块间插入分隔符

生成的文件只包含话术正文，无标题、无标签，可直接粘贴使用。

---

## 复用到新项目

复制一份 `rounds.yaml`，修改 `sections` 和 `rounds`，脚本不用改：

```bash
python3 generate_rounds.py new_project.yaml -o ./new_project_result
```

---

## 内置话术模块（示例）

当前 `rounds.yaml` 中预置了以下模块，适用于小程序 + 管理后台类项目：

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

## License

[MIT](./LICENSE) © [whyy9527](https://github.com/whyy9527)

可自由使用、修改和分发，但须保留原作者署名及指向本仓库的来源链接。
