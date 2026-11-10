"""Evidence-first analysis of synthetic CI logs; standard-library only."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Finding:
    category: str
    confidence: str
    evidence_id: str
    line_number: int
    excerpt: str
    next_step: str


@dataclass(frozen=True)
class Analysis:
    source: str
    findings: tuple[Finding, ...]
    summary: str


RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("dependency", re.compile(r"could not resolve|no matching distribution|package .* not found|dependency resolution failed", re.I),
     "Confirm the package name, version constraint, and configured package index."),
    ("test", re.compile(r"assertionerror|tests? failed|expected .+ (?:but )?got |test failure", re.I),
     "Inspect the failing test, its assertion, and the relevant recent code changes."),
    ("compilation", re.compile(r"syntaxerror|compilation failed|cannot find symbol|type error|build failed: compile", re.I),
     "Review the compiler diagnostic and check the affected source and dependency versions."),
    ("authentication", re.compile(r"unauthorized|authentication failed|invalid credentials|permission denied", re.I),
     "Check the intended identity, permission scope, and secret configuration without printing secrets."),
    ("timeout", re.compile(r"timed? out|timeout|deadline exceeded|operation exceeded .* seconds", re.I),
     "Check service availability and resource limits, then compare the step with a known-good run."),
)


def analyze_text(text: str, source: str = "<input>") -> Analysis:
    """Find known failure signatures and keep the exact supporting line."""
    findings: list[Finding] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        for category, pattern, next_step in RULES:
            if pattern.search(line):
                evidence_id = f"E{len(findings) + 1}"
                excerpt = line[:300]
                findings.append(Finding(category, "high", evidence_id, line_number, excerpt, next_step))
                break
    if not findings:
        summary = "No supported failure signature found. Review the log manually; the analyzer does not infer a cause without evidence."
    else:
        categories = sorted({finding.category for finding in findings})
        summary = f"Found {len(findings)} evidence-backed failure line(s) across {', '.join(categories)}."
    return Analysis(source, tuple(findings), summary)


def _validated_ai_summary(analysis: Analysis) -> str | None:
    """Ask a configured compatible endpoint to summarize findings, safely."""
    base_url = os.environ.get("AI_BASE_URL", "").rstrip("/")
    model = os.environ.get("AI_MODEL", "")
    api_key = os.environ.get("AI_API_KEY", "")
    if not (base_url and model and api_key):
        return None

    evidence = [{"id": f.evidence_id, "category": f.category, "line": f.line_number,
                 "excerpt": f.excerpt, "next_step": f.next_step} for f in analysis.findings]
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": (
                "Summarize only the supplied CI findings. Do not invent causes or claim a fix. "
                "Return JSON with keys summary and evidence_ids; evidence_ids must be chosen "
                "only from the supplied IDs."
            )},
            {"role": "user", "content": json.dumps(evidence)},
        ],
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        result = json.loads(content)
        summary = result.get("summary")
        returned_ids = result.get("evidence_ids")
        allowed_ids = {finding.evidence_id for finding in analysis.findings}
        if not isinstance(summary, str) or not summary.strip() or not isinstance(returned_ids, list):
            return None
        if not returned_ids or any(item not in allowed_ids for item in returned_ids):
            return None
        return summary.strip()[:1000] + " [AI summary; verify against cited evidence]"
    except (urllib.error.URLError, TimeoutError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _render_text(analysis: Analysis, summary: str | None = None) -> str:
    lines = [f"Source: {analysis.source}", f"Summary: {summary or analysis.summary}"]
    if not analysis.findings:
        return "\n".join(lines)
    lines.append("Findings:")
    for finding in analysis.findings:
        lines.extend((
            f"  {finding.evidence_id} | {finding.category} | {finding.confidence} | line {finding.line_number}",
            f"    Evidence: {finding.excerpt}",
            f"    Suggested next step: {finding.next_step}",
        ))
    return "\n".join(lines)


def _evaluate(path: Path) -> dict[str, Any]:
    totals: dict[str, int] = defaultdict(int)
    correct: dict[str, int] = defaultdict(int)
    predicted: dict[str, int] = defaultdict(int)
    rows = 0
    with path.open(encoding="utf-8") as corpus:
        for row_number, raw in enumerate(corpus, start=1):
            if not raw.strip():
                continue
            row = json.loads(raw)
            expected = row["expected"]
            analysis = analyze_text(row["log"], f"case-{row_number}")
            guess = analysis.findings[0].category if analysis.findings else "unknown"
            rows += 1
            totals[expected] += 1
            predicted[guess] += 1
            if guess == expected:
                correct[expected] += 1
    classes = sorted(set(totals) | set(predicted))
    per_class = {}
    for label in classes:
        tp = correct[label]
        precision = tp / predicted[label] if predicted[label] else 0.0
        recall = tp / totals[label] if totals[label] else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {"support": totals[label], "precision": precision, "recall": recall, "f1": f1}
    return {"cases": rows, "accuracy": sum(correct.values()) / rows if rows else 0.0, "per_class": per_class}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evidence-first analysis of synthetic CI failures")
    commands = parser.add_subparsers(dest="command", required=True)
    analyze_parser = commands.add_parser("analyze", help="analyze a text log")
    analyze_parser.add_argument("log_file", type=Path)
    analyze_parser.add_argument("--ai", action="store_true", help="request an optional configured model summary")
    analyze_parser.add_argument("--json", action="store_true", help="print machine-readable output")
    evaluate_parser = commands.add_parser("evaluate", help="score the offline classifier on labeled JSONL")
    evaluate_parser.add_argument("corpus", type=Path)
    args = parser.parse_args(argv)

    try:
        if args.command == "analyze":
            analysis = analyze_text(args.log_file.read_text(encoding="utf-8", errors="replace"), str(args.log_file))
            ai_summary = _validated_ai_summary(analysis) if args.ai else None
            if args.json:
                output = asdict(analysis)
                output["findings"] = [asdict(item) for item in analysis.findings]
                output["summary"] = ai_summary or analysis.summary
                print(json.dumps(output, indent=2))
            else:
                print(_render_text(analysis, ai_summary))
            return 0
        result = _evaluate(args.corpus)
        print(json.dumps(result, indent=2))
        return 0 if result["cases"] else 2
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
