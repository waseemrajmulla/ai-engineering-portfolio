"""Local TF-IDF retrieval and citation-grounded extractive answers."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)
DEFAULT_THRESHOLD = 0.12


@dataclass(frozen=True)
class Passage:
    document_id: str
    title: str
    sentence_number: int
    text: str
    terms: tuple[str, ...]


@dataclass(frozen=True)
class Match:
    passage: Passage
    score: float


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def load_passages(path: Path) -> list[Passage]:
    documents = json.loads(path.read_text(encoding="utf-8"))
    passages = []
    for document in documents:
        for sentence_number, sentence in enumerate(re.split(r"(?<=[.!?])\s+", document["text"]), start=1):
            terms = tuple(tokenize(sentence))
            if terms:
                passages.append(Passage(document["id"], document["title"], sentence_number, sentence, terms))
    return passages


class Retriever:
    def __init__(self, passages: list[Passage]):
        self.passages = passages
        document_frequency = Counter(term for passage in passages for term in set(passage.terms))
        count = max(1, len(passages))
        self.idf = {term: math.log(1 + count / (1 + frequency)) + 1 for term, frequency in document_frequency.items()}

    def rank(self, query: str) -> list[Match]:
        query_terms = tokenize(query)
        if not query_terms:
            return []
        query_counts = Counter(query_terms)
        query_vector = {term: count * self.idf.get(term, 0.0) for term, count in query_counts.items()}
        query_norm = math.sqrt(sum(value * value for value in query_vector.values()))
        matches = []
        for passage in self.passages:
            passage_counts = Counter(passage.terms)
            passage_vector = {term: count * self.idf.get(term, 0.0) for term, count in passage_counts.items()}
            passage_norm = math.sqrt(sum(value * value for value in passage_vector.values()))
            dot = sum(value * passage_vector.get(term, 0.0) for term, value in query_vector.items())
            score = dot / (query_norm * passage_norm) if query_norm and passage_norm else 0.0
            matches.append(Match(passage, score))
        return sorted(matches, key=lambda match: (-match.score, match.passage.document_id, match.passage.sentence_number))


def answer(query: str, retriever: Retriever, threshold: float = DEFAULT_THRESHOLD) -> dict[str, Any]:
    matches = retriever.rank(query)
    best = matches[0] if matches else None
    if best is None or best.score < threshold:
        return {"answer": "I do not have enough evidence in the local collection to answer that.", "abstained": True,
                "source": None, "score": best.score if best else 0.0}
    source = f"{best.passage.document_id}#{best.passage.sentence_number}"
    return {"answer": best.passage.text, "abstained": False, "source": source, "score": best.score,
            "title": best.passage.title}


def evaluate(corpus_path: Path, retriever: Retriever, threshold: float) -> dict[str, Any]:
    rows = [json.loads(line) for line in corpus_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    retrieval_hits = 0
    abstain_tp = abstain_fp = abstain_fn = 0
    for row in rows:
        result = answer(row["query"], retriever, threshold)
        expected_abstain = row["expected_abstain"]
        if result["abstained"] and expected_abstain:
            abstain_tp += 1
        elif result["abstained"]:
            abstain_fp += 1
        elif expected_abstain:
            abstain_fn += 1
        elif result["source"].split("#", 1)[0] == row["expected_document"]:
            retrieval_hits += 1
    answerable = sum(not row["expected_abstain"] for row in rows)
    precision = abstain_tp / (abstain_tp + abstain_fp) if abstain_tp + abstain_fp else 0.0
    recall = abstain_tp / (abstain_tp + abstain_fn) if abstain_tp + abstain_fn else 0.0
    return {
        "queries": len(rows),
        "answerable_queries": answerable,
        "top1_document_hit_rate": retrieval_hits / answerable if answerable else 0.0,
        "abstention_precision": precision,
        "abstention_recall": recall,
        "threshold": threshold,
        "note": "Metrics apply only to this synthetic fixture set.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Citation-grounded QA over a local synthetic corpus")
    subparsers = parser.add_subparsers(dest="command", required=True)
    answer_parser = subparsers.add_parser("answer", help="retrieve and cite one supporting passage")
    answer_parser.add_argument("query")
    answer_parser.add_argument("--documents", type=Path, default=Path("citation_qa_documents.json"))
    answer_parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    eval_parser = subparsers.add_parser("evaluate", help="measure retrieval and abstention")
    eval_parser.add_argument("corpus", type=Path)
    eval_parser.add_argument("--documents", type=Path, default=Path("citation_qa_documents.json"))
    eval_parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    args = parser.parse_args(argv)
    try:
        retriever = Retriever(load_passages(args.documents))
        if args.command == "answer":
            print(json.dumps(answer(args.query, retriever, args.threshold), indent=2))
        else:
            print(json.dumps(evaluate(args.corpus, retriever, args.threshold), indent=2))
        return 0
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
