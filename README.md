# Waseemraj M Mulla — AI Engineering Portfolio

Independent AI engineering projects focused on grounded outputs, evaluation, and human review. All bundled examples are synthetic. No employer source code, internal documents, customer data, or confidential corporate information is included.

## Projects

### AI Evidence Triage

A Python CLI that classifies common CI failure signatures, cites the exact log lines behind each finding, and suggests a safe next diagnostic step. An optional OpenAI-compatible model summarizes only the extracted findings; its evidence references are validated before display.

**Outcome:** turns noisy synthetic logs into reviewable, line-cited findings. The offline evaluator reports accuracy, precision, recall, and F1 on a small labeled fixture set; those scores describe only the included examples.

### Citation-Grounded QA

A local retrieval-augmented QA demo over a bounded synthetic knowledge base. It ranks source passages with TF-IDF, returns an extractive answer with a document citation, and abstains below a configurable confidence threshold.

**Outcome:** makes answer provenance visible and measures retrieval hit rate and abstention behavior against synthetic questions.

## Get the source

The complete runnable source for both demos is in [ai-engineering-portfolio-source.zip](ai-engineering-portfolio-source.zip). Extract the archive into a working directory and follow the README in each project folder. Both projects use Python 3.11+ and the standard library; the optional model summary requires an OpenAI-compatible endpoint and environment variables.

## Engineering focus

- Evidence-grounded LLM workflows and constrained model output
- Retrieval, citations, confidence thresholds, and abstention
- Reproducible evaluation with explicit limitations
- Privacy-conscious examples using synthetic data only
