
import hashlib
import json
import sqlite3
import uuid
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "researchpilot.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS papers (
                paper_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                content_hash TEXT NOT NULL UNIQUE,
                total_pages INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                paper_id TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                FOREIGN KEY (paper_id)
                    REFERENCES papers(paper_id)
                    ON DELETE CASCADE,
                UNIQUE (paper_id, page_number, chunk_index)
            );

            CREATE INDEX IF NOT EXISTS idx_chunks_paper
            ON chunks(paper_id);

            CREATE INDEX IF NOT EXISTS idx_chunks_page
            ON chunks(paper_id, page_number);
        """)


def split_into_chunks(text: str, chunk_size: int = 1000,
                      overlap: int = 150) -> list[str]:
    """Split text into overlapping character-based chunks."""
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Invalid chunk_size or overlap.")

    text = " ".join(text.split())
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])

        if end == len(text):
            break

        start = end - overlap

    return chunks


def save_paper(filename: str, pdf_bytes: bytes,
               extracted: dict) -> dict:
    """Store paper metadata and page-level text chunks."""
    content_hash = hashlib.sha256(pdf_bytes).hexdigest()

    # Avoid processing the same PDF into the database twice.
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT paper_id, filename, total_pages FROM papers "
            "WHERE content_hash = ?",
            (content_hash,),
        ).fetchone()

        if existing:
            return {
                "paper_id": existing["paper_id"],
                "filename": existing["filename"],
                "total_pages": existing["total_pages"],
                "duplicate": True,
            }

        paper_id = str(uuid.uuid4())
        chunks_to_save = []

        for page in extracted["pages"]:
            page_number = page["page_number"]

            for index, chunk_text in enumerate(
                split_into_chunks(page["text"])
            ):
                chunks_to_save.append((
                    str(uuid.uuid4()),
                    paper_id,
                    page_number,
                    index,
                    chunk_text,
                ))

        conn.execute(
            """
            INSERT INTO papers
                (paper_id, filename, content_hash, total_pages)
            VALUES (?, ?, ?, ?)
            """,
            (
                paper_id,
                filename,
                content_hash,
                extracted["total_pages"],
            ),
        )

        conn.executemany(
            """
            INSERT INTO chunks
                (chunk_id, paper_id, page_number, chunk_index, text)
            VALUES (?, ?, ?, ?, ?)
            """,
            chunks_to_save,
        )

    return {
        "paper_id": paper_id,
        "filename": filename,
        "total_pages": extracted["total_pages"],
        "chunks_created": len(chunks_to_save),
        "duplicate": False,
    }


def list_papers() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT p.paper_id, p.filename, p.total_pages,
                   p.created_at, COUNT(c.chunk_id) AS chunk_count
            FROM papers p
            LEFT JOIN chunks c ON c.paper_id = p.paper_id
            GROUP BY p.paper_id
            ORDER BY p.created_at DESC
        """).fetchall()

    return [dict(row) for row in rows]


def search_chunks(query: str, limit: int = 10) -> list[dict]:
    """Basic lexical search; semantic search comes later."""
    terms = query.split()
    if not terms:
        return []

    # Escape LIKE wildcards and treat each word as a required term.
    escaped_terms = [
        term.replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        for term in terms
    ]

    conditions = " AND ".join(["c.text LIKE ? ESCAPE '\\'"] * len(terms))
    parameters = [f"%{term}%" for term in escaped_terms]
    parameters.append(max(1, min(limit, 50)))

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT c.chunk_id, c.paper_id, p.filename,
                   c.page_number, c.text
            FROM chunks c
            JOIN papers p ON p.paper_id = c.paper_id
            WHERE {conditions}
            ORDER BY p.created_at DESC
            LIMIT ?
            """,
            parameters,
        ).fetchall()

    return [dict(row) for row in rows]
