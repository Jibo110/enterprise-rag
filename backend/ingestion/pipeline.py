import os

os.environ.setdefault("USER_AGENT", "enterprise-rag/1.0")

import uuid
from typing import List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain.schema import Document as LangchainDocument
from pinecone import Pinecone, ServerlessSpec
from sqlalchemy.orm import Session
from core.config import get_settings
from core.database import Document, DocumentStatus


settings = get_settings()


class DocumentIngestionPipeline:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            openai_api_key=settings.openai_api_key,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        existing = [idx.name for idx in self.pc.list_indexes()]
        if settings.pinecone_index_name not in existing:
            self.pc.create_index(
                name=settings.pinecone_index_name,
                dimension=settings.pinecone_dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            print(f"Created index: {settings.pinecone_index_name}")
        else:
            print(f"Index already exists: {settings.pinecone_index_name}")

    def _load_pdf(self, file_path: str) -> List[LangchainDocument]:
        loader = PyPDFLoader(file_path)
        return loader.load()

    def _load_url(self, url: str) -> List[LangchainDocument]:
        loader = WebBaseLoader(url)
        return loader.load()

    def _chunk_documents(
        self,
        docs: List[LangchainDocument],
        doc_id: str,
        source_name: str,
    ) -> List[LangchainDocument]:
        chunks = self.text_splitter.split_documents(docs)
        for i, chunk in enumerate(chunks):
            chunk.metadata.update(
                {
                    "doc_id": doc_id,
                    "source_name": source_name,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
            )
        return chunks

    def ingest_pdf(
        self,
        file_path: str,
        filename: str,
        db: Session,
        namespace: str = "default",
    ) -> str:
        doc_id = str(uuid.uuid4())
        db_doc = Document(
            id=doc_id,
            filename=filename,
            file_path=file_path,
            source_type="pdf",
            status=DocumentStatus.PROCESSING,
            namespace=namespace,
        )
        db.add(db_doc)
        db.commit()
        try:
            raw_docs = self._load_pdf(file_path)
            print(f"Loaded {len(raw_docs)} pages from {filename}")
            chunks = self._chunk_documents(raw_docs, doc_id, filename)
            print(f"Split into {len(chunks)} chunks")
            PineconeVectorStore.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                index_name=settings.pinecone_index_name,
                namespace=namespace,
            )
            print(f"Stored {len(chunks)} vectors in Pinecone")
            db_doc.status = DocumentStatus.READY
            db_doc.chunk_count = len(chunks)
            db.commit()
            return doc_id
        except Exception as e:
            db_doc.status = DocumentStatus.FAILED
            db_doc.error_message = str(e)
            db.commit()
            raise e

    def ingest_url(
        self,
        url: str,
        db: Session,
        namespace: str = "default",
    ) -> str:
        doc_id = str(uuid.uuid4())
        db_doc = Document(
            id=doc_id,
            filename=url,
            source_type="url",
            status=DocumentStatus.PROCESSING,
            namespace=namespace,
        )
        db.add(db_doc)
        db.commit()
        try:
            raw_docs = self._load_url(url)
            chunks = self._chunk_documents(raw_docs, doc_id, url)
            PineconeVectorStore.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                index_name=settings.pinecone_index_name,
                namespace=namespace,
            )
            db_doc.status = DocumentStatus.READY
            db_doc.chunk_count = len(chunks)
            db.commit()
            return doc_id
        except Exception as e:
            db_doc.status = DocumentStatus.FAILED
            db_doc.error_message = str(e)
            db.commit()
            raise e
