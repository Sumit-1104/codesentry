# CodeSentry

Multi-agent AI system for automated code review, built with LangGraph and free LLM inference via Groq.

## Overview

CodeSentry analyzes Python code using four specialized AI agents running in parallel, then aggregates their findings into a unified report. It combines traditional static analysis tools with LLM-based reasoning to catch issues that rule-based tools alone would miss.

## Features

- **Static Analysis Agent** — wraps `pylint` to detect code smells, unused imports, and style violations
- **Security Scanner Agent** — wraps `bandit` to identify vulnerabilities like hardcoded secrets and command injection risks
- **Documentation Generator Agent** — uses an LLM to write missing docstrings in PEP 257 style
- **Test Generator Agent** — uses an LLM to suggest pytest unit tests, including edge cases
- **Parallel orchestration** — all four agents run concurrently via LangGraph, sharing state and merging results into one report

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph |
| LLM inference | Groq (OpenAI-compatible API) |
| Static analysis | Pylint, Bandit |
| Backend | Django |
| Language | Python 3.12 |

## Architecture

Input (file/repo)
│
▼
┌─────────────────────────────┐
│ LangGraph Orchestrator │
│ (shared state, parallel) │
└──────────────┬───────────────┘
┌────────┼────────┬────────┐
▼ ▼ ▼ ▼
Static Security Doc Test
Analyzer Scanner Generator Generator
└────────┴────────┴────────┘
▼
Aggregator
▼
Unified Report


## Setup

1. Clone the repo:

git clone https://github.com/Sumit-1104/codesentry.git
cd codesentry


2. Create and activate a virtual environment:

python -m venv venv
venv\Scripts\activate


3. Install dependencies:

pip install -r requirements.txt


4. Add your Groq API key to a `.env` file:

GROQ_API_KEY=your_key_here


5. Run the orchestrator:

python -m core.orchestrator


## Roadmap

- [ ] RAG layer for cross-file codebase context (ChromaDB)
- [ ] Web dashboard for viewing reports
- [ ] GitHub Actions integration for automatic PR comments
- [ ] Evaluation framework with precision/recall benchmarks
- [ ] Docker deployment

## Why this project

Most code review tools are either purely rule-based (fast but rigid) or purely LLM-based (flexible but unpredictable). CodeSentry combines both: deterministic tools for what they're good at, and LLM reasoning for tasks like documentation and test generation where judgment matters more than fixed rules.