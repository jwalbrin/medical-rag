"""
Stage 1: Load PubMedQA JSON files into a SQLite database.

Schema design:
- `documents` table: the corpus to be retrieved over (abstract contexts).
  Populated from BOTH PQA-L and PQA-U, tagged by source split.
- `eval_questions` table: question + ground-truth answer pairs, used ONLY
  for evaluating retrieval/generation. Tagged by split so you can filter
  to PQA-L (trustworthy labels) at query time.
- Each eval question links to its "origin" document via origin_pubid, but
  this FK should be used for scoring ("did retrieval find the right doc?"),
  never fed into the retrieval step itself.
"""

import json
import sqlite3
import sys
from pathlib import Path

from .config import Settings


def create_schema(conn: sqlite3.Connection):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS documents (
        pubid           TEXT PRIMARY KEY,
        split           TEXT NOT NULL,
        context_text    TEXT NOT NULL,
        meshes          TEXT,
        year            TEXT
    );

    CREATE TABLE IF NOT EXISTS eval_questions (
        pubid           TEXT PRIMARY KEY,
        split           TEXT NOT NULL,
        question        TEXT NOT NULL,
        long_answer     TEXT,
        final_decision  TEXT,
        origin_pubid    TEXT NOT NULL,
        FOREIGN KEY (origin_pubid) REFERENCES documents(pubid)
    );

    CREATE INDEX IF NOT EXISTS idx_eval_split ON eval_questions(split);
    """)
    conn.commit()


def get_field(entry: dict, *candidates, default=None):
    """Try several possible key names/cases, since field casing has varied
    across released copies of this dataset (e.g. QUESTION vs question)."""
    for c in candidates:
        if c in entry:
            return entry[c]
    return default


def _inspect_sample(data: dict, n: int = 1):
    keys = list(data.keys())[:n]
    for k in keys:
        print(f"--- Sample entry: pubid={k} ---")
        print(json.dumps(data[k], indent=2)[:1500])
        print()


def load_split(conn: sqlite3.Connection, path: Path, split_label: str):
    with open(path) as f:
        data = json.load(f)

    print(f"\nLoaded {len(data)} entries from {path}")
    _inspect_sample(data, n=1)

    confirm = input(
        f"\nDoes the field structure above look right for split '{split_label}'? "
        f"[y to continue / n to abort]: "
    ).strip().lower()
    if confirm != "y":
        print("Aborting. Adjust get_field() calls and rerun.")
        sys.exit(1)

    doc_rows, eval_rows = [], []

    for pubid, entry in data.items():
        question = get_field(entry, "QUESTION", "question")
        contexts = get_field(entry, "CONTEXTS", "contexts", default=[])
        meshes = get_field(entry, "MESHES", "meshes", default=[])
        year = get_field(entry, "YEAR", "year")
        long_answer = get_field(entry, "LONG_ANSWER", "long_answer")
        final_decision = get_field(entry, "FINAL_DECISION", "final_decision")

        context_text = "\n\n".join(contexts) if isinstance(contexts, list) else str(contexts or "")

        if not question or not context_text:
            print(f"  [skip] pubid={pubid} missing question or context")
            continue

        doc_rows.append((pubid, split_label, context_text, json.dumps(meshes) if meshes else None, str(year) if year else None))
        eval_rows.append((pubid, split_label, question, long_answer, final_decision, pubid))

    conn.executemany(
        "INSERT OR REPLACE INTO documents (pubid, split, context_text, meshes, year) VALUES (?, ?, ?, ?, ?)",
        doc_rows,
    )
    conn.executemany(
        "INSERT OR REPLACE INTO eval_questions (pubid, split, question, long_answer, final_decision, origin_pubid) VALUES (?, ?, ?, ?, ?, ?)",
        eval_rows,
    )
    conn.commit()
    print(f"  Inserted {len(doc_rows)} documents and {len(eval_rows)} eval questions for split '{split_label}'.")


def run(settings: Settings):
    if not settings.pql and not settings.pqu:
        raise ValueError("At least one of PQL or PQU must be set.")

    conn = sqlite3.connect(settings.db)
    create_schema(conn)

    if settings.pql:
        load_split(conn, settings.pql, "L")
    if settings.pqu:
        load_split(conn, settings.pqu, "U")

    doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    eval_count = conn.execute("SELECT COUNT(*) FROM eval_questions").fetchone()[0]
    eval_l_count = conn.execute("SELECT COUNT(*) FROM eval_questions WHERE split='L'").fetchone()[0]

    print(f"\nDone. documents={doc_count}, eval_questions={eval_count} (split=L: {eval_l_count})")
    print(f"Database written to {settings.db}")
    conn.close()
