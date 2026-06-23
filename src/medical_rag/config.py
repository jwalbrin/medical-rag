from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()


@dataclass
class Settings:
    pql: Path | None = field(default_factory=lambda: Path(v) if (v := os.getenv("PQL")) else None)
    pqu: Path | None = field(default_factory=lambda: Path(v) if (v := os.getenv("PQU")) else None)
    db: Path = field(default_factory=lambda: Path(os.getenv("DB", "pubmedqa.db")))


settings = Settings()
