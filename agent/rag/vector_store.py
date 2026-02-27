import os
from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings

# Connection string - uses psycopg3 driver (sync mode for LangChain PGVector)
CONNECTION_STRING = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://ps03user:ps03password@localhost:5432/ps03db",
)


def get_vector_store() -> PGVector:
    """Returns the pgvector instance for the enterprise knowledge base."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    store = PGVector(
        embeddings=embeddings,
        collection_name="enterprise_knowledge",
        connection=CONNECTION_STRING,
        use_jsonb=True,
    )
    return store
