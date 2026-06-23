# medical-rag

Retrieval-augmented generation pipeline over [PubMedQA](https://pubmedqa.github.io/).

## Setup

If not installed, get uv: [uv](https://docs.astral.sh/uv/):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install the project:

```bash
uv sync
```

Activate the environment:

```bash
source .venv/bin/activate
```

## Configuration

Copy `.env.example` to `.env` and set paths for your data files:

```bash
cp .env.example .env
```

```ini
PQL=data/ori_pqal.json   # PubMedQA Labeled split
PQU=data/ori_pqau.json   # PubMedQA Unlabeled split
DB=pubmedqa.db            # output SQLite database
```

## Usage

Run individual pipeline stages:

```bash
medical-rag load                          # load JSON data into SQLite
medical-rag embed                         # embed documents into vector store
medical-rag query "what causes sepsis?"   # query the RAG pipeline
```

Run all stages end-to-end:

```bash
medical-rag pipeline
```

CLI args override `.env` values for a single run:

```bash
medical-rag load --pql other.json --db other.db
```

## Adding dependencies

```bash
uv add <package>        # add a runtime dependency
uv add --dev <package>  # add a dev-only dependency
```

This updates both `pyproject.toml` and `uv.lock`. Commit both files.
