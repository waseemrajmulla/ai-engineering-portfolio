# Waseemraj M Mulla — AI Engineering Portfolio

Independent AI engineering projects focused on grounded outputs, evaluation, and human review. All bundled examples are synthetic. No employer source code, internal documents, customer data, or confidential corporate information is included.

## Projects

### AI Evidence Triage

A Python CLI that classifies common CI failure signatures, cites the exact log lines behind each finding, and suggests a safe next diagnostic step. An optional OpenAI-compatible model summarizes the extracted findings; its evidence references are validated before display.

**Outcome:** converts noisy synthetic logs into concise, reviewable findings. The offline evaluator reports accuracy, precision, recall, and F1 on the small labeled fixture set; those scores apply only to these examples.

**Code and guide:** [Python source](ai_evidence_triage.py) · [Project README](README_AI_EVIDENCE_TRIAGE.md) · [Labeled synthetic cases](evidence_triage_golden.jsonl)

### Citation-Grounded QA

A local retrieval-augmented QA demo that ranks passages from a bounded synthetic knowledge base, returns an extractive answer with a document citation, and abstains below a configurable confidence threshold.

**Outcome:** makes answer provenance visible and measures retrieval hit rate and abstention behavior on labeled synthetic questions.

**Code and guide:** [Python source](citation_grounded_qa.py) · [Project README](README_CITATION_GROUNDED_QA.md) · [Synthetic documents](citation_qa_documents.json) · [Evaluation queries](citation_qa_queries.jsonl)

## Quick start

Run these commands from the repository root with Python 3.11+:

```bash
python3 ai_evidence_triage.py analyze evidence_triage_dependency_failure.log
python3 ai_evidence_triage.py evaluate evidence_triage_golden.jsonl
python3 citation_grounded_qa.py answer "How do I use an idempotency key for retries?"
python3 citation_grounded_qa.py evaluate citation_qa_queries.jsonl
```

Both projects use the Python standard library. The optional model summary for AI Evidence Triage requires an OpenAI-compatible endpoint and environment variables. See that project's README before using the feature.

## Engineering focus

- Evidence-grounded LLM workflows and constrained model output
- Retrieval, citations, confidence thresholds, and abstention
- Reproducible evaluation with explicit limitations
- Privacy-conscious examples using synthetic data only

[Download the complete source bundle](ai-engineering-portfolio-source.zip)
