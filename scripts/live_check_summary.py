#!/usr/bin/env python3
"""
Description: Condenses a Weaver live-check JSON report into a readable conformance summary.
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

import json
import sys
from collections import Counter
from typing import Any, Iterator

ACME_NAMESPACE = "acme."
_TOP_FINDINGS = 15


def iter_advice(node: Any) -> Iterator[dict]:
    """Yield every advice entry in the report, wherever it is nested.

    The report mirrors the shape of the telemetry it graded, so advice appears
    at resource, span, metric, log and attribute level. Walking the whole tree
    is simpler, and cheap enough, compared to encoding that shape here.

    Args:
        node: Any fragment of the decoded report.

    Yields:
        Each advice dict found under a `live_check_result.all_advice` list.
    """
    if isinstance(node, dict):
        result = node.get("live_check_result")
        if isinstance(result, dict):
            yield from result.get("all_advice", [])
        for value in node.values():
            yield from iter_advice(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_advice(item)


def describe(advice: dict) -> str:
    """Return a stable one-line label for grouping identical findings."""
    context = advice.get("context") or {}
    subject = (
        context.get("attribute_key")
        or context.get("metric_name")
        or context.get("event_name")
        or advice.get("signal_name")
        or "-"
    )
    return f"{advice.get('id')} :: {subject}"


def main(path: str) -> int:
    """Print the summary for the report at `path`.

    Args:
        path: Path to the JSON report produced by `weaver registry live-check`.

    Returns:
        0 on success, 1 if the report cannot be read.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            report = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        print(f"cannot read live-check report at {path}: {error}", file=sys.stderr)
        return 1

    stats = report.get("statistics", {})
    print("=== Registry conformance ===")
    print(f"samples graded    : {len(report.get('samples', []))}")
    print(f"registry coverage : {stats.get('registry_coverage', 0):.1%}")
    print(f"total advisories  : {stats.get('total_advisories', 0)}")
    print(f"by level          : {stats.get('advice_level_counts', {})}")
    print()

    findings = Counter(describe(advice) for advice in iter_advice(report))

    print(f"=== Findings on '{ACME_NAMESPACE}*' telemetry ===")
    acme = {key: count for key, count in findings.items() if ACME_NAMESPACE in key}
    if acme:
        for key, count in sorted(acme.items(), key=lambda item: -item[1]):
            print(f"{count:6d}  {key}")
    else:
        print("none — every Acme signal matched the registry")
    print()

    print(f"=== Top {_TOP_FINDINGS} findings overall ===")
    for key, count in findings.most_common(_TOP_FINDINGS):
        print(f"{count:6d}  {key}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "report/live-check.json"))
