#!/usr/bin/env python3
"""Append Pocketbook ledger events from structured payloads."""

from __future__ import annotations

import argparse
import json
import sys

from ledger_common import (
    LedgerError,
    append_event,
    build_create_event,
    build_revert_event,
    build_update_event,
    entry_response,
    json_dump,
    load_events,
    load_payload,
    materialize_entries,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Append events to a Pocketbook ledger.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("create", "update", "revert"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--data-dir", default=None, help="Ledger data root.")
        subparser.add_argument(
            "--payload",
            default="-",
            help="Path to a JSON payload file, or - to read JSON from stdin.",
        )

    args = parser.parse_args()
    try:
        payload = load_payload(args.payload)
        events = load_events(args.data_dir)
        if args.command == "create":
            result = build_create_event(payload, events)
        elif args.command == "update":
            result = build_update_event(payload, events)
        else:
            result = build_revert_event(payload, events)
        append_event(args.data_dir, result["event"])
        entries = materialize_entries(events + [result["event"]])
        response = {
            "ok": True,
            "event": result["event"],
            "entry": entry_response(entries[result["event"]["entry_id"]]),
        }
        if args.command == "create":
            response["duplicate_candidates"] = result["duplicate_candidates"]
        print(json_dump(response))
        return 0
    except (LedgerError, json.JSONDecodeError) as exc:
        print(json_dump({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
