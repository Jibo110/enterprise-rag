from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import uuid
import os
import json

from core.config import get_settings
from core.database import get_db, create_tables, Document, DocumentStatus
from ingestion.pipeline import DocumentIngestionPipeline
from retrieval.engine import RetrievalEngine

settings = get_settings()

app = FastAPI(
    title="Enterprise RAG System",
    description="Multi-source document Q&A with citations",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ingestion_pipeline = DocumentIngestionPipeline()
retrieval_engine = RetrievalEngine()


class QueryRequest(BaseModel):
    question: str
    namespace: str = "default"
    filter_doc_ids: Optional[List[str]] = None
    stream: bool = False


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    chunks_used: int


class URLIngestRequest(BaseModel):
    url: str
    namespace: str = "default"


@app.on_event("startup")
async def startup_event():
    create_tables()
    print("Database tables ready")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/documents/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    namespace: str = "default",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail=f"Only PDF files supported. Got: {file.filename}"
        )

    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = f"{temp_dir}/{uuid.uuid4()}_{file.filename}"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    def process_in_background():
        try:
            ingestion_pipeline.ingest_pdf(
                file_path=file_path,
                filename=file.filename,
                db=db,
                namespace=namespace,
            )
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    background_tasks.add_task(process_in_background)

    return {
        "message": "PDF upload started. Processing in background.",
        "filename": file.filename,
        "status": "processing",
    }


@app.post("/documents/ingest-url")
async def ingest_url(
    request: URLIngestRequest,
    db: Session = Depends(get_db),
):
    try:
        doc_id = ingestion_pipeline.ingest_url(
            url=request.url,
            db=db,
            namespace=request.namespace,
        )
        return {
            "doc_id": doc_id,
            "url": request.url,
            "status": "ready",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents(
    namespace: str = "default",
    db: Session = Depends(get_db),
):
    docs = db.query(Document).filter(Document.namespace == namespace).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status.value,
            "chunk_count": doc.chunk_count,
            "source_type": doc.source_type,
            "created_at": str(doc.created_at),
        }
        for doc in docs
    ]


@app.get("/documents/{doc_id}")
async def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": doc.id,
        "filename": doc.filename,
        "status": doc.status.value,
        "chunk_count": doc.chunk_count,
        "error_message": doc.error_message,
    }


@app.post("/query")
async def query_documents(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    result = await retrieval_engine.query(
        question=request.question,
        namespace=request.namespace,
        filter_doc_ids=request.filter_doc_ids,
    )
    return result


@app.post("/query/stream")
async def stream_query(request: QueryRequest):
    async def generate():
        async for token in retrieval_engine.stream_query(
            question=request.question,
            namespace=request.namespace,
        ):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
