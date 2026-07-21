from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document as LangchainDocument
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from core.config import get_settings

settings = get_settings()

RAG_SYSTEM_PROMPT = """You are an intelligent document assistant.

Answer questions using ONLY the context provided below.

Rules:
1. Use ONLY the provided context. Do NOT use outside knowledge.
2. If context is insufficient say: "I don't have enough information in the provided documents."
3. Always cite sources at the end: **Sources:** [Document Name, Page X]
4. Be concise. Use bullet points for lists.

Context:
{context}

Question: {question}

Answer:"""


class RetrievalEngine:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            openai_api_key=settings.openai_api_key,
        )

        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            openai_api_key=settings.openai_api_key,
            streaming=True,
        )

        self.vector_store = PineconeVectorStore(
            index_name=settings.pinecone_index_name,
            embedding=self.embeddings,
            pinecone_api_key=settings.pinecone_api_key,
        )

    def _format_context(self, docs: List[LangchainDocument]) -> str:
        parts = []
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source_name", "Unknown")
            page = doc.metadata.get("page", "")
            page_str = f", Page {page + 1}" if page != "" else ""
            parts.append(f"[Source {i + 1}: {source}{page_str}]\n{doc.page_content}")
        return "\n\n---\n\n".join(parts)

    def _extract_sources(self, docs: List[LangchainDocument]) -> List[Dict]:
        seen = set()
        sources = []
        for doc in docs:
            source_name = doc.metadata.get("source_name", "Unknown")
            page = doc.metadata.get("page", None)
            doc_id = doc.metadata.get("doc_id", "")
            key = f"{doc_id}_{page}"
            if key not in seen:
                seen.add(key)
                sources.append(
                    {
                        "name": source_name,
                        "page": page + 1 if page is not None else None,
                        "doc_id": doc_id,
                    }
                )
        return sources

    def retrieve(
        self,
        query: str,
        namespace: str = "default",
        filter_doc_ids: Optional[List[str]] = None,
    ) -> List[LangchainDocument]:
        kwargs = {
            "k": settings.retrieval_top_k,
            "namespace": namespace,
        }
        if filter_doc_ids:
            kwargs["filter"] = {"doc_id": {"$in": filter_doc_ids}}
        docs_with_scores = self.vector_store.similarity_search_with_score(
            query, **kwargs
        )
        relevant_docs = [doc for doc, score in docs_with_scores if score >= 0.7]
        return relevant_docs[: settings.retrieval_final_k]

    async def query(
        self,
        question: str,
        namespace: str = "default",
        filter_doc_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        relevant_docs = self.retrieve(question, namespace, filter_doc_ids)
        if not relevant_docs:
            return {
                "answer": "I couldn't find relevant information in the uploaded documents.",
                "sources": [],
                "chunks_used": 0,
            }
        context = self._format_context(relevant_docs)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", RAG_SYSTEM_PROMPT),
                ("human", "{question}"),
            ]
        )
        chain = prompt | self.llm | StrOutputParser()
        answer = await chain.ainvoke(
            {
                "context": context,
                "question": question,
            }
        )
        sources = self._extract_sources(relevant_docs)
        return {
            "answer": answer,
            "sources": sources,
            "chunks_used": len(relevant_docs),
        }

    async def stream_query(
        self,
        question: str,
        namespace: str = "default",
    ) -> AsyncGenerator[str, None]:
        relevant_docs = self.retrieve(question, namespace)
        if not relevant_docs:
            yield "I couldn't find relevant information in the documents."
            return
        context = self._format_context(relevant_docs)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", RAG_SYSTEM_PROMPT),
                ("human", "{question}"),
            ]
        )
        chain = prompt | self.llm | StrOutputParser()
        async for token in chain.astream(
            {
                "context": context,
                "question": question,
            }
        ):
            yield token
