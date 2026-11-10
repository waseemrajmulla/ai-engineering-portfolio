# AI Evidence Triage

An evidence-first assistant for explaining synthetic CI failures. It groups common failure signatures, cites the exact log lines behind its diagnosis, and can optionally ask an OpenAI-compatible model to produce a concise summary. The deterministic analyzer works offline; model output is treated as untrusted and its evidence references are checked before display.

This is an independent portfolio project. All bundled examples are synthetic. It contains no employer data, internal logs, customer data, credentials, or proprietary prompts.

## Why it is useful

CI output is noisy, while a useful first response needs to answer three questions: what failed, what evidence supports that conclusion, and what should an engineer inspect next? This project turns a raw log into a short, reviewable report and keeps the underlying evidence visible.

## What it does

- Detects dependency resolution, test assertion, compilation, authentication, and timeout failures.
- Preserves line numbers and short evidence excerpts for each finding.
- Produces a conservative next-step suggestion tied to the detected failure class.
- Optionally summarizes findings with an OpenAI-compatible chat-completions endpoint.
- Validates model-returned evidence IDs; unsupported IDs are discarded.
- Evaluates the offline classifier against a small, hand-labeled synthetic corpus and prints accuracy by class.
- Runs on Python 3.11+ with no required third-party packages.

## Quick start

```bash
python3 ai_evidence_triage.py analyze evidence_triage_dependency_failure.log
python3 ai_evidence_triage.py evaluate evidence_triage_golden.jsonl
```

Example output:

```text
Category: dependency
Confidence: high (signature match)
Evidence:
  [E1] line 4: ERROR: Could not resolve package 'sample-lib==9.9.9'
Suggested next step: Confirm the package name, version constraint, and configured package index.
```

The bundled corpus is intentionally small and synthetic. Its evaluation score describes only those examples; it is not a claim about production performance.

## Optional model summary

The model receives only the findings extracted from the input file. Do not point this demo at private or company logs. Configure an endpoint and model that you control:

```bash
export AI_BASE_URL="https://your-openai-compatible-host/v1"
export AI_MODEL="your-model-name"
export AI_API_KEY="your-key"
python3 ai_evidence_triage.py analyze evidence_triage_test_failure.log --ai
```

`AI_API_KEY` is read from the environment and is never printed or written to disk. The model is asked for a JSON summary plus evidence IDs. The tool checks those IDs against the analyzer's findings and falls back to the deterministic summary if the response is malformed or unsupported.

## Commands

```text
python3 -m src.triagekit analyze <log-file> [--ai] [--json]
python3 -m src.triagekit evaluate <jsonl-file>
```

## Evaluation design

Each JSONL row contains a synthetic log and an expected category. The evaluator reports overall accuracy and per-category precision, recall, and F1. The rules are transparent and intentionally modest: this gives a reproducible baseline before adding a learned classifier or comparing model-assisted variants. Expand the corpus with balanced, synthetic edge cases before drawing conclusions.

## Design notes

1. **Evidence before prose:** the deterministic pass creates findings and evidence references before any model call.
2. **Constrained model role:** the optional model summarizes provided findings; it does not inspect arbitrary external systems or execute suggested actions.
3. **Human review:** suggested next steps are diagnostic prompts, never automated remediations.
4. **Privacy by default:** no telemetry, persistence, or external call is made unless `--ai` is explicitly selected.

## Project outcome

The working demo turns noisy synthetic build output into categorized findings with line-level evidence and measurable offline evaluation. It demonstrates an auditable AI workflow, safe LLM integration, and a baseline that can be improved with an expanded labeled corpus. Any performance claim should be generated from a larger, independently reviewed evaluation set.

## Roadmap

- Add configurable rule packs and user-provided, sanitized fixtures.
- Compare the rules-only baseline with a model-assisted classifier on a held-out synthetic set.
- Add a small local web UI for uploading a log and inspecting evidence.
- Add regression tests and CI once the first public iteration is reviewed.

## License

MIT. See [LICENSE](LICENSE).
