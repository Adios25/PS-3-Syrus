from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from langchain_core.documents import Document

from .vector_store import get_vector_store


def _read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:
        raise RuntimeError("PDF ingestion requires 'pypdf'. Install it in agent requirements.") from exc

    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n".join([page for page in pages if page])


def load_documents_from_paths(paths: Iterable[Path]) -> List[Document]:
    documents: List[Document] = []
    for path in paths:
        suffix = path.suffix.lower()
        if suffix == ".md":
            content = _read_markdown(path)
        elif suffix == ".pdf":
            content = _read_pdf(path)
        else:
            continue

        if not content.strip():
            continue

        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": path.name,
                    "format": suffix.lstrip("."),
                },
            )
        )
    return documents


def ingest_documents(paths: Iterable[str]) -> int:
    file_paths = [Path(path).expanduser().resolve() for path in paths]
    docs = load_documents_from_paths(file_paths)
    store = get_vector_store()
    if hasattr(store, "add_documents"):
        store.add_documents(docs)
    return len(docs)


if __name__ == "__main__":
    # Example:
    # python -m rag.ingest ~/docs/setup_guides.pdf ~/docs/onboarding_faq.md
    import sys

    count = ingest_documents(sys.argv[1:])
    print(f"Ingested {count} documents.")
