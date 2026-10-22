# ResearchPilot Architecture

ResearchPilot is an AI-powered research paper assistant that combines PDF processing, semantic retrieval, and locally hosted language models.

## System Architecture

```mermaid
flowchart TD
    U[User] <--> UI[Frontend: HTML, CSS, JavaScript]

    UI <--> API[FastAPI Backend]

    API --> PDF[PDF Processing: PyMuPDF]
    API --> DB[(SQLite Database)]
    API --> SS[Semantic Search]

    PDF --> DB
    DB --> SS

    SS --> EMB[Sentence Transformers]
    EMB --> VEC[384-Dimensional Embeddings]
    VEC --> SS

    SS --> QA[Question Answering Service]
    SS --> COMP[Paper Comparison Service]

    QA <--> OLL[Ollama: Llama 3.2 3B]
    COMP <--> OLL

    QA --> CIT[Evidence and Citations]
    COMP --> CIT

    CIT --> API