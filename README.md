# Pocketbook

Pocketbook is a conversational personal-ledger skill focused on daily bookkeeping flow rather than generic expense reporting.

It is designed for:

- quick natural-language capture
- incomplete entries that can be fixed later
- local JSONL persistence plus a readable Markdown view
- safe correction through `update` and `revert` events instead of rewriting history

## What It Does

Pocketbook centers on four actions:

- quick capture: `午饭28`, `地铁4元`, `工资到账12000`
- query and summary: `今天花了多少`, `最近三笔`, `本月餐饮多少`
- completion: fill in payment method, account, category, merchant, or note later
- correction: `改上一笔`, `撤销上一笔`

## Storage Model

The ledger is append-only.

- `ledger.jsonl` is the source of truth
- `personal_finance.md` is a derived human-readable snapshot

Records are stored as events:

- `create`
- `update`
- `revert`

## Repository Layout

- `SKILL.md`: skill definition, trigger rules, workflow, and script usage
- `agents/openai.yaml`: UI-facing skill metadata
- `references/schema.md`: ledger event schema and query semantics
- `references/intent-examples.md`: trigger examples and non-trigger examples
- `scripts/`: append, query, edit-recent, and Markdown rendering utilities

## Local Smoke Test

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

## ClawHub Notes

Current ClawHub publishing uses `SKILL.md` plus supporting text files. It does not require a separate `manifest.yaml`.

Typical publish flow:

```bash
bun clawhub login
bun clawhub publish . --slug pocketbook --name "Pocketbook" --version 0.1.0 --tags latest --changelog "Initial release"
```

Per ClawHub policy, published skills are distributed under `MIT-0`.
