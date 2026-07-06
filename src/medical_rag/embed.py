"""Stage 2: Embed documents from SQLite into a ChromaDB vector store."""

import sqlite3

import chromadb
from sentence_transformers import SentenceTransformer

from .config import Settings

EMBED_BATCH_SIZE = 256


class ChromaStore:
    def __init__(self, path: str, collection_name: str):
        self._client = chromadb.PersistentClient(path=path)
        self._col = self._client.get_or_create_collection(collection_name)

    def search(self, query_embedding: list[float], n_results: int) -> list[dict]:
        results = self._col.query(
            query_embeddings=[query_embedding], n_results=n_results
        )
        return [
            {"id": id_, "text": doc, "metadata": meta, "distance": dist}
            for id_, doc, meta, dist in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]


def get_store(settings: Settings) -> ChromaStore:
    return ChromaStore(str(settings.chroma_path), settings.collection_name)


def run(settings: Settings) -> None:

    print(f"Loading embedding model '{settings.embed_model}'...")
    model = SentenceTransformer(settings.embed_model)
    store = get_store(settings)

    print(f"Fetching data from database...")
    conn = sqlite3.connect(settings.db)
    rows = conn.execute(
        "SELECT pubid, split, context_text, meshes, year FROM documents"
    ).fetchall()
    conn.close()

    if not rows:
        raise RuntimeError(
            f"No documents found in {settings.db}. Run 'medical-rag load' first."
        )

    print(f"Embedding {len(rows)} documents...")
    ids = [r[0] for r in rows]
    texts = [r[2] for r in rows]
    metadatas = [
        {"split": r[1], "meshes": r[3] or "", "year": r[4] or ""} for r in rows
    ]

    for i in range(0, len(rows), EMBED_BATCH_SIZE):
        batch_ids = ids[i : i + EMBED_BATCH_SIZE]
        batch_texts = texts[i : i + EMBED_BATCH_SIZE]
        batch_metas = metadatas[i : i + EMBED_BATCH_SIZE]

        embeddings = model.encode(batch_texts, show_progress_bar=False).tolist()

        existing = set(store._col.get(ids=batch_ids)["ids"])
        new = [
            (id_, emb, text, meta)
            for id_, emb, text, meta in zip(
                batch_ids, embeddings, batch_texts, batch_metas
            )
            if id_ not in existing
        ]
        if new:
            new_ids, new_embs, new_texts, new_metas = zip(*new)
            store._col.add(
                ids=list(new_ids),
                embeddings=list(new_embs),
                documents=list(new_texts),
                metadatas=list(new_metas),
            )
        print(f"  {min(i + EMBED_BATCH_SIZE, len(rows))}/{len(rows)}", end="\r")

    print(f"\nDone. {len(rows)} documents embedded into '{settings.chroma_path}'.")
