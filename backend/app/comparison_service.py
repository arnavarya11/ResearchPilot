
import json
import urllib.error
import urllib.request

from backend.app.semantic_search import search_semantic


OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2:3b"


def compare_papers(
    question: str,
    filename_a: str,
    filename_b: str,
    limit_per_paper: int = 4,
) -> dict:
    """Compare two papers using retrieved evidence and local AI."""

    question = question.strip()
    filename_a = filename_a.strip()
    filename_b = filename_b.strip()

    if not question:
        raise ValueError("Comparison question cannot be empty.")

    if not filename_a or not filename_b:
        raise ValueError("Select two papers to compare.")

    if filename_a == filename_b:
        raise ValueError("Please select two different papers.")

    if not 1 <= limit_per_paper <= 10:
        raise ValueError("Limit must be between 1 and 10.")

    evidence_by_paper = {}

    for filename in (filename_a, filename_b):
        results = search_semantic(
            question,
            limit=limit_per_paper,
            filename=filename,
        )

        evidence_by_paper[filename] = [
            {
                "filename": result["filename"],
                "page_number": result["page_number"],
                "chunk_id": result["chunk_id"],
                "text": result["text"],
                "similarity": result["similarity"],
            }
            for result in results
        ]

    # Number the evidence passages so the model can cite them.
    evidence_sections = []

    for filename, passages in evidence_by_paper.items():
        evidence_sections.append(f"PAPER: {filename}")

        for index, passage in enumerate(passages, start=1):
            evidence_sections.append(
                f"[{filename} - E{index}]\n"
                f"Page: {passage['page_number']}\n"
                f"Passage: {passage['text']}"
            )

    evidence_text = "\n\n".join(evidence_sections)

    prompt = f"""
Compare these two research papers using ONLY the evidence below.

Comparison question:
{question}

Evidence:
{evidence_text}

Write your response with these headings:
1. Research objective
2. Methodology
3. Key findings
4. Limitations and research gaps
5. Overall comparison

Rules:
- Do not invent facts, metrics, results, or references.
- Cite evidence using its exact identifier, for example [RP2.pdf - E1].
- Clearly distinguish evidence from inference.
- If evidence for a category is missing, say "Not established by the retrieved passages."
- Do not claim one paper is better without supporting evidence.
- Keep the comparison clear and useful for academic research.
"""

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a careful academic research assistant. "
                    "Compare only the supplied evidence. Never invent "
                    "citations, findings, or page numbers."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            model_response = json.loads(response.read().decode("utf-8"))

    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Could not connect to Ollama. Make sure Ollama is running."
        ) from exc

    citations = []

    for filename, passages in evidence_by_paper.items():
        for index, passage in enumerate(passages, start=1):
            citations.append(
                {
                    "citation_id": f"{filename} - E{index}",
                    **passage,
                }
            )

    return {
        "question": question,
        "paper_a": filename_a,
        "paper_b": filename_b,
        "comparison": model_response["message"]["content"],
        "citations": citations,
        "evidence_count": len(citations),
    }
