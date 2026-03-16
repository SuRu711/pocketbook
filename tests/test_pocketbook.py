from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PYTHON = sys.executable


def run_json_script(script_name: str, *args: str, payload: dict | None = None) -> dict:
    proc = subprocess.run(
        [PYTHON, str(SCRIPTS / script_name), *args],
        input=json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"Command failed: {script_name} {' '.join(args)}\n"
            f"stdout={proc.stdout.decode('utf-8', errors='replace')}\n"
            f"stderr={proc.stderr.decode('utf-8', errors='replace')}"
        )
    return json.loads(proc.stdout.decode("utf-8"))


class PocketbookTests(unittest.TestCase):
    def test_idempotent_create_reuses_existing_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = {
                "source_text": "午饭28",
                "amount": "28",
                "entry_type": "expense",
                "category": "food",
                "payment_method": "wechat",
                "account": "cmb",
                "idempotency_key": "retry-001",
            }
            first = run_json_script("append_ledger.py", "create", "--data-dir", tmp, "--payload", "-", payload=payload)
            second = run_json_script("append_ledger.py", "create", "--data-dir", tmp, "--payload", "-", payload=payload)
            recent = run_json_script("query_ledger.py", "recent", "--data-dir", tmp, "--limit", "10")

            self.assertFalse(first["reused_existing"])
            self.assertTrue(second["reused_existing"])
            self.assertEqual(first["entry"]["entry_id"], second["entry"]["entry_id"])
            self.assertEqual(len(recent["entries"]), 1)

    def test_update_last_targets_last_recorded_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = run_json_script(
                "append_ledger.py",
                "create",
                "--data-dir",
                tmp,
                "--payload",
                "-",
                payload={
                    "source_text": "今天咖啡20",
                    "amount": "20",
                    "entry_type": "expense",
                    "category": "coffee",
                    "payment_method": "wechat",
                    "account": "cmb",
                },
            )
            second = run_json_script(
                "append_ledger.py",
                "create",
                "--data-dir",
                tmp,
                "--payload",
                "-",
                payload={
                    "source_text": "补记昨天午饭30",
                    "amount": "30",
                    "entry_type": "expense",
                    "occurred_at": "2026-03-15T12:00:00+08:00",
                    "category": "food",
                    "payment_method": "alipay",
                    "account": "cmb",
                },
            )
            updated = run_json_script(
                "edit_recent.py",
                "update-last",
                "--data-dir",
                tmp,
                "--payload",
                "-",
                payload={
                    "source_text": "把上一笔备注改一下",
                    "changes": {"note": "backfilled entry"},
                },
            )

            self.assertEqual(first["entry"]["entry_id"] != second["entry"]["entry_id"], True)
            self.assertEqual(updated["entry"]["entry_id"], second["entry"]["entry_id"])
            self.assertEqual(updated["entry"]["note"], "backfilled entry")

    def test_stale_lock_is_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock_path = Path(tmp) / ".ledger.lock"
            lock_path.write_text("stale-lock", encoding="utf-8")
            stale_time = time.time() - 600
            os.utime(lock_path, (stale_time, stale_time))

            result = run_json_script(
                "append_ledger.py",
                "create",
                "--data-dir",
                tmp,
                "--payload",
                "-",
                payload={
                    "source_text": "地铁4元",
                    "amount": "4",
                    "entry_type": "expense",
                    "category": "transport",
                },
            )

            self.assertTrue(result["ok"])
            self.assertFalse(lock_path.exists())

    def test_profile_defaults_and_aliases_apply_on_create(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = {
                "defaults": {
                    "currency": "CNY",
                    "payment_method": "wechat",
                    "account": "cmb",
                },
                "aliases": {
                    "category": {"餐饮": "food"},
                    "payment_method": {"微信": "wechat"},
                    "account": {"招行": "cmb"},
                },
            }
            (Path(tmp) / "profile.json").write_text(
                json.dumps(profile, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            result = run_json_script(
                "append_ledger.py",
                "create",
                "--data-dir",
                tmp,
                "--payload",
                "-",
                payload={
                    "source_text": "餐饮28 微信",
                    "amount": "28",
                    "entry_type": "expense",
                    "category": "餐饮",
                    "payment_method": "微信",
                },
            )

            self.assertEqual(result["entry"]["category"], "food")
            self.assertEqual(result["entry"]["payment_method"], "wechat")
            self.assertEqual(result["entry"]["account"], "cmb")
            self.assertEqual(result["entry"]["currency"], "CNY")

    def test_concurrent_retries_with_same_idempotency_key_create_one_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = {
                "source_text": "午饭28",
                "amount": "28",
                "entry_type": "expense",
                "category": "food",
                "payment_method": "wechat",
                "account": "cmb",
                "idempotency_key": "concurrent-001",
            }
            results: list[dict] = []
            errors: list[str] = []
            start = threading.Event()

            def worker() -> None:
                try:
                    start.wait()
                    results.append(
                        run_json_script(
                            "append_ledger.py",
                            "create",
                            "--data-dir",
                            tmp,
                            "--payload",
                            "-",
                            payload=payload,
                        )
                    )
                except Exception as exc:  # pragma: no cover - surfaced in assertion below
                    errors.append(str(exc))

            threads = [threading.Thread(target=worker) for _ in range(2)]
            for thread in threads:
                thread.start()
            start.set()
            for thread in threads:
                thread.join()

            self.assertFalse(errors, "\n".join(errors))
            recent = run_json_script("query_ledger.py", "recent", "--data-dir", tmp, "--limit", "10")

            self.assertEqual(len(results), 2)
            self.assertEqual(len(recent["entries"]), 1)
            self.assertEqual(sum(1 for item in results if item["reused_existing"]), 1)


if __name__ == "__main__":
    unittest.main()
