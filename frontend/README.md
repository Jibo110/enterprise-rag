# Enterprise RAG System

A production-grade Retrieval-Augmented Generation system. Upload PDFs and URLs, ask questions in natural language, get cited answers powered by GPT-4o-mini and Pinecone vector search.

Built by **Jibran Khan** — Senior Full-Stack & AI Engineer

---

## Live Demo

> Coming soon — deploying to AWS

---

## Architecture

All pushed. 10 commits on GitHub. Everything is safe.

README first

Open README.md in the root of enterprise-rag — the one Next.js didn't touch. Delete everything in it and type this:

markdown

# Enterprise RAG System

A production-grade Retrieval-Augmented Generation system. Upload PDFs and URLs, ask questions in natural language, get cited answers powered by GPT-4o-mini and Pinecone vector search.

Built by **Jibran Khan** — Senior Full-Stack & AI Engineer

---

## Live Demo

> Coming soon — deploying to AWS

---

## Architecture

┌─────────────────┐ ┌──────────────────┐ ┌─────────────┐
│ Next.js UI │────▶│ FastAPI Backend │────▶│ OpenAI │
│ (TypeScript) │ │ (Python) │ │ GPT-4o-mini│
└─────────────────┘ └────────┬─────────┘ └─────────────┘
│
┌────────────┴────────────┐
▼ ▼
┌──────────────┐ ┌──────────────────┐
│ Pinecone │ │ PostgreSQL │
│ Vector Store │ │ (Document Meta) │
└──────────────┘ └──────────────────┘

---

## Tech Stack

| Layer            | Technology                       | Purpose                     |
| ---------------- | -------------------------------- | --------------------------- |
| Frontend         | Next.js 16, TypeScript, Tailwind | Chat UI with streaming      |
| Backend          | FastAPI, Python 3.12             | REST API + async processing |
| AI/LLM           | OpenAI GPT-4o-mini               | Answer generation           |
| Embeddings       | OpenAI text-embedding-3-small    | Text → vectors              |
| Vector DB        | Pinecone (Serverless)            | Semantic search             |
| Database         | PostgreSQL                       | Document metadata           |
| Containerization | Docker                           | Local development           |

---

## Features

- Upload PDFs and ingest URLs into a vector knowledge base
- Ask questions in natural language
- Streaming responses — tokens appear as they're generated
- Source citations — every answer references exact document and page
- Multi-tenant namespaces — isolate different users' documents
- Background processing — large PDFs processed asynchronously
- Relevance filtering — cosine similarity threshold for accurate retrieval

---

## Project Structure

enterprise-rag/
├── backend/
│ ├── core/
│ │ ├── config.py # Environment settings via pydantic
│ │ └── database.py # PostgreSQL models and connection
│ ├── ingestion/
│ │ └── pipeline.py # PDF/URL loading, chunking, embedding
│ ├── retrieval/
│ │ └── engine.py # Vector search + LLM answer generation
│ └── main.py # FastAPI app and all endpoints
├── frontend/
│ └── app/
│ ├── components/
│ │ ├── FileUpload.tsx # PDF upload with drag and drop
│ │ ├── ChatWindow.tsx # Message list with auto-scroll
│ │ ├── MessageBubble.tsx # Single message with markdown
│ │ └── SourceCard.tsx # Citation display
│ └── page.tsx # Main chat interface
└── docker-compose.yml # PostgreSQL container

---

## How RAG Works

INGEST
PDF → extract pages → split into 1000-char chunks
→ embed each chunk (1536 numbers) → store in Pinecone
QUERY
Question → embed question → find 10 nearest chunks in Pinecone
→ filter by similarity score → send top 4 chunks + question to GPT
→ stream answer with citations back to user

---

## Local Setup

**Prerequisites:** Python 3.12, Node.js 18+, Docker, OpenAI API key, Pinecone API key

**Backend:**

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # Add your API keys
docker-compose up -d         # Start PostgreSQL
uvicorn main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**API docs:** `http://localhost:8000/docs`
**Frontend:** `http://localhost:3000`

---

## API Endpoints

| Method | Endpoint                | Description                |
| ------ | ----------------------- | -------------------------- |
| GET    | `/health`               | Server health check        |
| POST   | `/documents/upload-pdf` | Upload and ingest PDF      |
| POST   | `/documents/ingest-url` | Ingest a webpage           |
| GET    | `/documents`            | List all documents         |
| POST   | `/query`                | Ask a question             |
| POST   | `/query/stream`         | Ask a question (streaming) |

---

## Roadmap

- [ ] Add OpenAI credits and test full end-to-end
- [ ] Deploy backend to AWS EC2
- [ ] Deploy frontend to Vercel
- [ ] Add authentication
- [ ] Add document deletion
- [ ] Support more file types (DOCX, CSV)

---

_Built as part of a public AI engineering learning journey — July 2026_
