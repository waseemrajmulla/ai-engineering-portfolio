# Citation-Grounded QA

A small, local retrieval-augmented QA demo that answers from a bounded document collection and points to the source passage for every answer. The included content is synthetic and intentionally short. No API keys, vector database, third-party packages, or network connection are needed.

## Why this project

An AI answer is easier to review when a reader can see where it came from. This demo separates retrieval from answer rendering, exposes retrieval scores, and returns an abstention when the best match is too weak.

## Features

- Sentence-level indexing with deterministic tokenization and TF-IDF cosine ranking.
- Answers quote only a short sentence from a retrieved passage and include its document ID.
- A configurable similarity threshold controls abstention.
- A labeled synthetic query set measures top-1 retrieval hit rate and abstention precision/recall.
- Local-only execution using Python 3.11+ and the standard library.

## Quick start

```bash
python3 citation_grounded_qa.py answer "How do I use an idempotency key for retries?"
python3 citation_grounded_qa.py evaluate citation_qa_queries.jsonl
```

Example:

```text
Answer: Use an idempotency key so retries can be recognized as the same operation.
Source: retry-safety#1 (similarity=0.47)
```

## Project outcome

The demo makes retrieval evidence visible, gives low-confidence questions a clear abstention, and produces reproducible retrieval and abstention metrics on a small synthetic evaluation set. Those metrics describe only this fixture corpus; they should not be generalized to other content or users.

## Data and privacy

All included documents and questions are fictional examples. The application reads local JSON files and does not transmit queries or documents to a service.

## Limitations

TF-IDF retrieval is a transparent baseline, not semantic search. Short queries, paraphrases, and domain vocabulary may rank poorly. The answer is an extractive sentence, not generated synthesis. A production system would need a representative held-out corpus, stronger retrieval, access controls, and human review.

## License

MIT. See [LICENSE](LICENSE).
