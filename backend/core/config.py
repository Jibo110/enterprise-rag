from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    pinecone_api_key: str
    pinecone_index_name: str = "enterprise-rag"
    pinecone_dimension: int = 1536

    database_url: str
    app_env: str = "development"
    app_secret: str = "changethis123"
    retrieval_top_k: int = 10
    retrieval_final_k: int = 4

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
