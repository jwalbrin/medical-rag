"""Stage 3: Retrieve relevant documents and generate an answer via Claude or a local LLM."""

import anthropic
import urllib.request
import json
from sentence_transformers import SentenceTransformer

from .config import Settings
from .embed import ChromaStore, get_store


SYSTEM_PROMPT = """You are a medical research assistant. Answer the question using only
the provided PubMed abstract excerpts. If the excerpts do not contain enough information
to answer confidently, say so. Cite the pubmed ID (pubid) of any excerpt you draw from."""


def retrieve(question: str, settings: Settings, store: ChromaStore | None = None) -> list[dict]:
    model = SentenceTransformer(settings.embed_model)
    query_embedding = model.encode(question).tolist()
    store = store or get_store(settings)
    return store.search(query_embedding, n_results=settings.n_results)


def _generate_anthropic(question: str, context: str, settings: Settings) -> str:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Abstracts:\n{context}\n\nQuestion: {question}"}],
    )
    return message.content[0].text


def _generate_llamacpp(question: str, context: str, settings: Settings) -> str:
    # llama.cpp server exposes an OpenAI-compatible /v1/chat/completions endpoint
    payload = json.dumps({
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Abstracts:\n{context}\n\nQuestion: {question}"},
        ],
        "max_tokens": 1024,
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        f"{settings.llm_base_url}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"]


def generate(question: str, hits: list[dict], settings: Settings) -> str:
    context = "\n\n".join(f"[pubid={h['id']}]\n{h['text']}" for h in hits)
    if settings.llm_backend == "llamacpp":
        return _generate_llamacpp(question, context, settings)
    return _generate_anthropic(question, context, settings)


def run(settings: Settings, question: str) -> None:
    print(f"Retrieving top {settings.n_results} documents...")
    hits = retrieve(question, settings)

    for i, h in enumerate(hits, 1):
        print(f"  {i}. pubid={h['id']} distance={h['distance']:.4f}")

    print("\nGenerating answer...\n")
    answer = generate(question, hits, settings)
    print(answer)
