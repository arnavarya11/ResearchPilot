# ResearchPilot

**An AI-powered research paper assistant for searching, understanding, and comparing scientific papers.**

ResearchPilot is a web application that helps users explore research papers through semantic search, evidence-based question answering, and AI-assisted paper comparison. It combines a Python backend, a searchable paper library, sentence embeddings, and a locally running language model.

## Features

- **PDF Upload:** Upload research papers and extract text from PDF documents.
- **Research Library:** Store and browse uploaded papers.
- **Semantic Search:** Retrieve relevant passages based on meaning rather than exact keyword matches.
- **Ask AI:** Ask questions about research papers and receive answers with supporting excerpts and page references.
- **Compare Papers:** Compare two papers using retrieved evidence.
- **Export Reports:** Export reports as Markdown or save them as PDF through browser printing.
- **Local AI Inference:** Use Ollama to run the language model locally.
- **Input Validation:** Reject unsupported file types and PDFs larger than the configured 20 MB limit.

## Technology Stack

| Component | Technology |
|---|---|
| Backend API | Python, FastAPI |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite |
| PDF Processing | PyMuPDF |
| Semantic Embeddings | Sentence Transformers |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Local Language Model | Ollama with `llama3.2:3b` |

## Architecture

1. A user uploads a PDF through the web interface.
2. The backend extracts text and stores paper information and text chunks in SQLite.
3. Sentence Transformers converts text chunks into embeddings.
4. Semantic search retrieves passages relevant to a user's question.
5. The local language model generates an answer or comparison using the retrieved evidence.
6. The interface displays the response and supporting citations.

## Prerequisites

- Windows, macOS, or Linux
- Python 3.11
- Ollama
- The Ollama model `llama3.2:3b`

## Run Locally

### 1. Clone or open the project

Open a terminal in the project root directory.

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

If a `requirements.txt` file exists, run:

```powershell
pip install -r requirements.txt
```

If your dependency file is located elsewhere, use its actual path.

### 4. Start Ollama

Install Ollama if necessary, then download the model:

```powershell
ollama pull llama3.2:3b
```

Make sure the Ollama service is running before using AI features.

### 5. Start the backend

From the project root:

```powershell
python -m uvicorn backend.app.main:app --reload
```

### 6. Open ResearchPilot

- Web application: http://127.0.0.1:8000/
- API documentation: http://127.0.0.1:8000/docs

Keep the backend terminal running while using the application.

## Testing

The following behaviors have been manually checked during development:

- PDF uploads and duplicate-upload handling
- Invalid-file and file-size validation
- Semantic search and page references
- AI question answering and evidence citations
- Comparison reports for two papers
- Markdown and PDF exports
- Persistence after backend restart
- Empty-input validation
- Graceful handling of an Ollama outage
- Main dashboard navigation and end-to-end workflows

These are manual test results, not a claim of comprehensive automated test coverage.

## Current Limitations

- Retrieval relevance may vary depending on the question and paper.
- AI-generated answers should be verified against the original paper.
- The current setup is designed primarily for local use.
- Automated evaluation, comprehensive automated tests, and deployment hardening remain future improvements.

## Future Improvements

- Automated retrieval and answer-quality benchmarks
- Automated API and regression tests
- Improved retrieval and chunking strategies
- More detailed evaluation of citation faithfulness
- Secure multi-user support
- Deployment and production monitoring

## Responsible Use

ResearchPilot is an assistive research tool. Users should verify important claims, citations, and interpretations against the original research papers rather than treating AI-generated responses as authoritative.

## License

No license has been specified yet. Add an appropriate license before distributing the project publicly.

## Project Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the system architecture diagram, component responsibilities, technology stack, and data flow.

## Project Documentation

- [README](README.md) — Overview, features, setup, and usage
- [Architecture](ARCHITECTURE.md) — System design and data flow
- [API Documentation](http://127.0.0.1:8000/docs) — Available when the backend is running locally
