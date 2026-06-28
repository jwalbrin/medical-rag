import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # data paths
    pql: Path | None = field(default_factory=lambda: Path(v) if (v := os.getenv("PQL")) else None)
    pqu: Path | None = field(default_factory=lambda: Path(v) if (v := os.getenv("PQU")) else None)
    db: Path = field(default_factory=lambda: Path(os.getenv("DB", "pubmedqa.db")))

    # vector store
    chroma_path: Path = field(default_factory=lambda: Path(os.getenv("CHROMA_PATH", "chroma_db")))
    collection_name: str = field(default_factory=lambda: os.getenv("COLLECTION_NAME", "pubmedqa"))
    embed_model: str = field(default_factory=lambda: os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2"))

    # generation
    anthropic_api_key: str | None = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    claude_model: str = field(default_factory=lambda: os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"))
    n_results: int = field(default_factory=lambda: int(os.getenv("N_RESULTS", "5")))


settings = Settings()
