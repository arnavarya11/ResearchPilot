
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model = None


def get_model():
    """Load the embedding model once and reuse it."""
    global _model

    if _model is None:
        print("Loading ResearchPilot embedding model...")
        _model = SentenceTransformer(MODEL_NAME)

    return _model


def generate_embedding(text: str) -> list[float]:
    """Convert text into a normalized 384-dimensional vector."""
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    vector = get_model().encode(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    return vector.tolist()


if __name__ == "__main__":
    sample = (
        "Vision Transformers process image patches using self-attention."
    )

    embedding = generate_embedding(sample)

    print("Model:", MODEL_NAME)
    print("Embedding dimensions:", len(embedding))
    print("First five values:", embedding[:5])
