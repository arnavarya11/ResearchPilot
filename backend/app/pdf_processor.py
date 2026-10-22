
from pathlib import Path
import pymupdf  # PyMuPDF


def extract_pdf_text(pdf_path: str) -> dict:
    """Extract text from a PDF while preserving page numbers."""

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("The uploaded file must be a PDF.")

    pages = []

    with pymupdf.open(path) as document:
        for page_index, page in enumerate(document):
            text = page.get_text("text").strip()

            pages.append({
                "page_number": page_index + 1,
                "text": text,
            })

    return {
        "filename": path.name,
        "total_pages": len(pages),
        "pages": pages,
        "full_text": "\n\n".join(
            page["text"] for page in pages
        ),
    }


if __name__ == "__main__":
    result = extract_pdf_text("data/sample.pdf")

    print("Filename:", result["filename"])
    print("Total pages:", result["total_pages"])
    print("\nFirst 1000 characters:\n")
    print(result["full_text"][:1000])
