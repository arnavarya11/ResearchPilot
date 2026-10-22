from backend.app.semantic_search import search_semantic
from pathlib import Path
from tempfile import NamedTemporaryFile
from backend.app.semantic_search import index_existing_chunks
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from backend.app.comparison_service import compare_papers
from fastapi.responses import FileResponse
from backend.app.qa_service import answer_question
from backend.app.database import (
    init_db,
    list_papers,
    save_paper,
    search_chunks,
)
from backend.app.pdf_processor import extract_pdf_text


app = FastAPI(
    title="ResearchPilot API",
    description="Upload, store, and search research papers.",
    version="0.2.0",
)

init_db()

@app.get("/")
def root():
    frontend_file = (
        Path(__file__).resolve().parents[2]
        / "frontend"
        / "index.html"
    )
    return FileResponse(frontend_file)



@app.post("/papers/upload")
async def upload_paper(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF file.")

    max_size = 20 * 1024 * 1024
    content = await file.read(max_size + 1)

    if len(content) > max_size:
        raise HTTPException(413, "PDF must be 20 MB or smaller.")

    if not content.startswith(b"%PDF-"):
        raise HTTPException(400, "The uploaded file is not a valid PDF.")

    temp_path = None

    try:
        with NamedTemporaryFile(suffix=".pdf", delete=False) as temp:
            temp.write(content)
            temp_path = Path(temp.name)

        extracted = extract_pdf_text(str(temp_path))

        if not extracted["full_text"].strip():
            raise HTTPException(
                422,
                "No extractable text found. The PDF may be scanned.",
            )

        result = save_paper(file.filename, content, extracted)

        if not result["duplicate"]:
            index_existing_chunks()

        return {
            **result,
            "message": (
                "Paper already exists in the database."
                if result["duplicate"]
                else "Paper uploaded and indexed successfully."
            ),
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            422,
            "Could not process or store this PDF.",
        ) from exc
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)



@app.get("/papers")
def get_papers():
    return {"papers": list_papers()}


@app.get("/search")
def search_papers(
    q: str = Query(..., min_length=1, max_length=300),
    limit: int = Query(10, ge=1, le=50),
):
    results = search_chunks(q, limit)

    return {
        "query": q,
        "results_count": len(results),
        "results": results,
    }


@app.get("/semantic-search")
def semantic_search_endpoint(
    q: str,
    limit: int = 5,
    filename: str | None = None,
):
    """Search research papers by meaning."""
    if not q.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty.",
        )

    if limit < 1 or limit > 20:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 20.",
        )

    try:
        results = search_semantic(q, limit, filename=filename)
        return {
        "query": q,
        "filename_filter": filename,
        "result_count": len(results),
        "results": results,
}
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

class AskRequest(BaseModel):
    question: str
    filename: str | None = None
    limit: int = 5


@app.post("/ask")
def ask_endpoint(request: AskRequest):
    question = request.question.strip()

    if not question:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    if not 1 <= request.limit <= 10:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 10.",
        )

    try:
        return answer_question(
            question=question,
            limit=request.limit,
            filename=request.filename,
        )
    except RuntimeError as exc:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

class CompareRequest(BaseModel):
    question: str
    filename_a: str
    filename_b: str
    limit_per_paper: int = 4


@app.post("/compare")
def compare_endpoint(request: CompareRequest):
    from fastapi import HTTPException

    try:
        return compare_papers(
            question=request.question,
            filename_a=request.filename_a,
            filename_b=request.filename_b,
            limit_per_paper=request.limit_per_paper,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
