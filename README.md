# Pocketbook

Pocketbook is a conversational personal-ledger skill focused on daily bookkeeping flow rather than generic expense reporting.

Pocketbook 是一个偏向日常对话流的个人记账 skill，重点不是做复杂报表，而是让用户可以随口快记、晚点补全、并且安全纠错。

## English

### What It Does

Pocketbook centers on four actions:

- quick capture: `午饭28`, `地铁4元`, `工资到账12000`
- query and summary: `今天花了多少`, `最近三笔`, `本月餐饮多少`
- completion: fill in payment method, account, category, merchant, or note later
- correction: `改上一笔`, `撤销上一笔`

It is designed for:

- quick natural-language capture
- incomplete entries that can be fixed later
- local JSONL persistence plus a readable Markdown view
- safe correction through `update` and `revert` events instead of rewriting history

### Storage Model

The ledger is append-only.

- `ledger.jsonl` is the source of truth
- `personal_finance.md` is a derived human-readable snapshot

Records are stored as events:

- `create`
- `update`
- `revert`

### Repository Layout

- `SKILL.md`: skill definition, trigger rules, workflow, and script usage
- `agents/openai.yaml`: UI-facing skill metadata
- `references/schema.md`: ledger event schema and query semantics
- `references/intent-examples.md`: trigger examples and non-trigger examples
- `scripts/`: append, query, edit-recent, profile management, and Markdown rendering utilities

### Local Smoke Test

Create a temporary data directory and append a record:

```powershell
$tmp = New-Item -ItemType Directory -Path (Join-Path $env:TEMP "pocketbook-demo") -Force
@'
{
  "source_text": "午饭28",
  "amount": "28.00",
  "entry_type": "expense",
  "category": "food",
  "payment_method": "unknown",
  "account": "unknown"
}
'@ | python .\scripts\append_ledger.py create --data-dir $tmp.FullName --payload -
```

Query the current summary:

```powershell
python .\scripts\query_ledger.py summary --data-dir $tmp.FullName --period today
```

Render the Markdown snapshot:

```powershell
python .\scripts\render_finance_md.py --data-dir $tmp.FullName
```

### ClawHub Notes

Current ClawHub publishing uses `SKILL.md` plus supporting text files. It does not require a separate `manifest.yaml`.

Typical publish flow:

```bash
bun clawhub login
bun clawhub publish . --slug pocketbook --name "Pocketbook" --version 0.1.0 --tags latest --changelog "Initial release"
```

Per ClawHub policy, published skills are distributed under `MIT-0`.

## 中文说明

### 这个 Skill 是做什么的

Pocketbook 主要围绕四类动作：

- 快记：`午饭28`、`地铁4元`、`工资到账12000`
- 查询汇总：`今天花了多少`、`最近三笔`、`本月餐饮多少`
- 晚点补全：支付方式、账户、分类、商户、备注等字段可以后补
- 纠错撤销：`改上一笔`、`撤销上一笔`

它的设计重点是：

- 支持自然语言低打断快记
- 允许信息缺失，先落盘再补全
- 使用本地 JSONL 持久化，并生成可读的 Markdown 视图
- 修改和撤销通过事件追加完成，不直接覆盖历史

### 存储方式

账本是 append-only 的：

- `ledger.jsonl` 是事实源
- `personal_finance.md` 是派生的可读视图

每一条操作都会记录成事件：

- `create`
- `update`
- `revert`

### 仓库结构

- `SKILL.md`：skill 定义、触发规则、工作流、脚本用法
- `agents/openai.yaml`：UI 层技能元数据
- `references/schema.md`：账本事件 schema 和查询口径
- `references/intent-examples.md`：触发样例和不应触发的样例
- `scripts/`：落盘、查询、改最近一笔、管理 profile、生成 Markdown 的脚本

### 本地快速验证

先创建一个临时数据目录，再追加一笔记录：

```powershell
$tmp = New-Item -ItemType Directory -Path (Join-Path $env:TEMP "pocketbook-demo") -Force
@'
{
  "source_text": "午饭28",
  "amount": "28.00",
  "entry_type": "expense",
  "category": "food",
  "payment_method": "unknown",
  "account": "unknown"
}
'@ | python .\scripts\append_ledger.py create --data-dir $tmp.FullName --payload -
```

查询今天的汇总：

```powershell
python .\scripts\query_ledger.py summary --data-dir $tmp.FullName --period today
```

生成 Markdown 账本视图：

```powershell
python .\scripts\render_finance_md.py --data-dir $tmp.FullName
```

### ClawHub 发布说明

按当前文档，ClawHub 发布以 `SKILL.md` 和相关文本文件为主，不需要单独的 `manifest.yaml`。

典型发布命令：

```bash
bun clawhub login
bun clawhub publish . --slug pocketbook --name "Pocketbook" --version 0.1.0 --tags latest --changelog "Initial release"
```

根据 ClawHub 当前规则，发布到平台上的 skill 会按 `MIT-0` 分发。
