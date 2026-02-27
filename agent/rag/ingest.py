from langchain_core.documents import Document
from .vector_store import get_vector_store

def ingest_mock_documents():
    """
    Mocks an ingestion pipeline.
    In real usage, this reads from PDF, Confluence, or GitHub Markdown.
    """
    store = get_vector_store()
    
    docs = [
        Document(
            page_content="To set up your environment, install Node.js 20 and Python 3.11. Run `npx create-next-app` for frontend.",
            metadata={"source": "engineering-setup-guide", "role": "developer"}
        ),
        Document(
            page_content="Use PostgreSQL for all relational data. Request DB credentials via Jira ticket ONB-REQ.",
            metadata={"source": "database-standards", "role": "developer"}
        ),
        Document(
            page_content="Design requests are handled in Figma. Marketing team members need a Figma Pro license.",
            metadata={"source": "design-tools", "role": "designer"}
        )
    ]
    
    # store.add_documents(docs)
    print(f"Mocked ingestion of {len(docs)} enterprise documents.")

if __name__ == "__main__":
    ingest_mock_documents()
