
import json
import sqlite3

import numpy as np

from backend.app.database import DATA_DIR
from backend.app.embedding_service import generate_embedding


DB_PATH = DATA_DIR / "researchpilot.db"



def init_embedding_table():
    """Create the embedding table with the correct chunk ID type."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS chunk_embeddings (
                chunk_id TEXT PRIMARY KEY,
                embedding TEXT NOT NULL,
                FOREIGN KEY (chunk_id)
                    REFERENCES chunks(chunk_id)
                    ON DELETE CASCADE
            )
        """)
        connection.commit()





def index_existing_chunks():
    """Embed chunks that have not yet been indexed."""
    init_embedding_table()

    with sqlite3.connect(DB_PATH) as connection:
        chunks = connection.execute("""
            SELECT c.chunk_id, c.text
            FROM chunks AS c
            LEFT JOIN chunk_embeddings AS e
                ON c.chunk_id = e.chunk_id
            WHERE e.chunk_id IS NULL
        """).fetchall()

        for chunk_id, chunk_text in chunks:
            if not chunk_text or not chunk_text.strip():
                continue

            embedding = generate_embedding(chunk_text)

            connection.execute("""
                INSERT OR IGNORE INTO chunk_embeddings
                    (chunk_id, embedding)
                VALUES (?, ?)
            """, (chunk_id, json.dumps(embedding)))

        connection.commit()

    return len(chunks)


def search_semantic(
    query: str,
    limit: int = 5,
    filename: str | None = None,
):
    """Rank paper chunks by semantic similarity."""
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    limit = max(1, min(limit, 20))

    query_embedding = np.array(
        generate_embedding(query),
        dtype=np.float32,
    )

    init_embedding_table()
    index_existing_chunks()

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute("""
            SELECT
                c.chunk_id,
                c.paper_id,
                c.page_number,
                c.chunk_index,
                c.text,
                p.filename,
                e.embedding
            FROM chunk_embeddings AS e
            JOIN chunks AS c ON c.chunk_id = e.chunk_id
            JOIN papers AS p ON p.paper_id = c.paper_id
            WHERE (? IS NULL OR p.filename = ?)
        """, (filename, filename)).fetchall()

    results = []

    for row in rows:
        stored_embedding = np.array(
            json.loads(row["embedding"]),
            dtype=np.float32,
        )

        score = float(np.dot(query_embedding, stored_embedding))

        results.append({
            "chunk_id": row["chunk_id"],
            "paper_id": row["paper_id"],
            "filename": row["filename"],
            "page_number": row["page_number"],
            "chunk_index": row["chunk_index"],
            "text": row["text"],
            "similarity": round(score, 4),
        })

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True,
    )

    return results[:limit]



 
if __name__ == "__main__":
    indexed = index_existing_chunks()
    print(f"Chunks newly indexed: {indexed}")

    query = input("Enter a research question: ").strip()

    if query:
        results = search_semantic(query)

        print("\nSemantic search results:\n")

        for number, result in enumerate(results, start=1):
            print(f"{number}. {result['filename']}")
            print(f"   Page: {result['page_number']}")
            print(f"   Similarity: {result['similarity']}")
            print(f"   Text: {result['text'][:300]}")
            print()
