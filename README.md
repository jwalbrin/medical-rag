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

## Using a local LLM (llama.cpp)

As an alternative to the Anthropic API you can serve a model locally via
[llama.cpp](https://github.com/ggml-org/llama.cpp). It exposes an OpenAI-compatible
HTTP API so no extra client library is needed.

### 1. Choose a model

Set `LLM_MODEL` in `.env` to any GGUF model on HuggingFace using the `repo:filename-prefix` format. Recommended options, roughly ordered by quality vs. speed:

| Model | `LLM_MODEL` value | VRAM | Notes |
|---|---|---|---|
| Gemma 4 4B (default) | `unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL` | ~4 GB | Best quality, slower |
| Qwen 2.5 3B | `bartowski/Qwen2.5-3B-Instruct-GGUF:Q4_K_M` | ~2 GB | Good balance of speed and quality |
| Llama 3.2 3B | `bartowski/Llama-3.2-3B-Instruct-GGUF:Q4_K_M` | ~2 GB | Well-tested, reliable |
| Phi-3.5 Mini 3.8B | `bartowski/Phi-3.5-mini-instruct-GGUF:Q4_K_M` | ~2.5 GB | Strong reasoning for its size |
| Gemma 3 1B | `bartowski/gemma-3-1b-it-GGUF:Q4_K_M` | ~1 GB | Fastest, noticeable quality drop |

### 2. Configure .env

```ini
LLM_BACKEND=llamacpp
LLM_BASE_URL=http://localhost:8080
LLM_MODEL=bartowski/Qwen2.5-3B-Instruct-GGUF:Q4_K_M  # or any model from the table above
LLAMACPP_IMAGE=ghcr.io/ggml-org/llama.cpp:full-cuda   # optional override
```

`HOST_PORT` is parsed automatically from `LLM_BASE_URL`, so there is no separate port variable.

### 2. Start the server

```bash
scripts/serve_llm.sh
```

This pulls the image and model on first run (model cached in `~/.cache/huggingface`) then starts the server. To preview the docker command without running it:

```bash
scripts/serve_llm.sh --dry-run
```

Verify the server is ready:

```bash
curl http://localhost:8080/health
```

### 3. Query

```bash
medical-rag query "Which is the best acuity test for people with amblyopia?"
```

No API key required.

### 4. Stop the server

```bash
scripts/stop_llm.sh
```

Switch back to Claude at any time by setting `LLM_BACKEND=anthropic` (the default).

## Adding dependencies

```bash
uv add <package>        # add a runtime dependency
uv add --dev <package>  # add a dev-only dependency
```

This updates both `pyproject.toml` and `uv.lock`. Commit both files.

TODO
Long form text
- chunking strategies
- reranker model
