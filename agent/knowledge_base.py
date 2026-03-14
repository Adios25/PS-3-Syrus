from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set, Tuple
import re


RESOURCE_DIR = Path(__file__).resolve().parent / "resources" / "ps03"

# Tier-1 searchable files from the official PS03 dataset.
RAG_FILES = (
    "company_overview.md",
    "engineering_standards.md",
    "architecture_documentation.md",
    "setup_guides.md",
    "policies.md",
    "org_structure.md",
    "onboarding_faq.md",
)

ROLE_HINTS = {
    "company_overview.md": {"backend", "frontend", "devops"},
    "engineering_standards.md": {"backend", "frontend", "devops"},
    "architecture_documentation.md": {"backend", "frontend", "devops"},
    "setup_guides.md": {"backend", "frontend", "devops"},
    "policies.md": {"backend", "frontend", "devops"},
    "org_structure.md": {"backend", "frontend", "devops"},
    "onboarding_faq.md": {"backend", "frontend", "devops"},
}

STACK_HINTS = {
    "company_overview.md": {"python", "node", "java", "react", "aws", "kubernetes"},
    "engineering_standards.md": {"python", "node", "typescript", "react", "java"},
    "architecture_documentation.md": {"python", "node", "java", "kafka", "redis", "postgresql"},
    "setup_guides.md": {"python", "node", "react", "java", "docker"},
    "policies.md": {"aws", "vpn"},
    "org_structure.md": {"backend", "frontend", "devops"},
    "onboarding_faq.md": {"python", "node", "react", "docker", "vpn"},
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "where",
    "with",
}


@dataclass(frozen=True)
class KnowledgeDoc:
    source_id: str
    title: str
    section: str
    content: str
    roles: Tuple[str, ...]
    stacks: Tuple[str, ...]
    source_file: str


@dataclass(frozen=True)
class IndexedDoc:
    doc: KnowledgeDoc
    tokens: Set[str]


def _tokenize(text: str) -> Set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in STOPWORDS and len(token) > 2
    }


def _extract_document_id(text: str, fallback: str) -> str:
    match = re.search(r"Document ID:\s*([A-Z0-9-]+)", text)
    if match:
        return match.group(1)
    return fallback


def _extract_title(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    return fallback


def _split_sections(markdown: str) -> List[Tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^##+\s+(.+)$", markdown))
    sections: List[Tuple[str, str]] = []

    if not matches:
        body = markdown.strip()
        if body:
            sections.append(("Overview", body))
        return sections

    for idx, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
        body = markdown[start:end].strip()
        if body:
            sections.append((heading, body))

    return sections


@lru_cache(maxsize=1)
def _load_index() -> Tuple[IndexedDoc, ...]:
    indexed_docs: List[IndexedDoc] = []

    for file_name in RAG_FILES:
        file_path = RESOURCE_DIR / file_name
        if not file_path.exists():
            continue

        text = file_path.read_text(encoding="utf-8")
        source_id = _extract_document_id(text, fallback=file_name.replace(".md", "").upper())
        title = _extract_title(text, fallback=file_name.replace("_", " ").title())
        sections = _split_sections(text)

        for heading, body in sections:
            doc = KnowledgeDoc(
                source_id=source_id,
                title=title,
                section=heading,
                content=body,
                roles=tuple(sorted(ROLE_HINTS.get(file_name, set()))),
                stacks=tuple(sorted(STACK_HINTS.get(file_name, set()))),
                source_file=file_name,
            )
            tokens = _tokenize(f"{title} {heading} {body}")
            indexed_docs.append(IndexedDoc(doc=doc, tokens=tokens))

    return tuple(indexed_docs)


def retrieve_documents(
    query: str,
    role: Optional[str] = None,
    stacks: Optional[Sequence[str]] = None,
    top_k: int = 3,
) -> List[KnowledgeDoc]:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    stack_set = {stack.lower() for stack in (stacks or [])}
    scored: List[Tuple[float, KnowledgeDoc]] = []

    for indexed in _load_index():
        overlap = len(query_tokens.intersection(indexed.tokens))
        if overlap == 0:
            continue

        score = float(overlap)
        if role and role.lower() in indexed.doc.roles:
            score += 1.0
        if stack_set and stack_set.intersection(indexed.doc.stacks):
            score += 0.75

        scored.append((score, indexed.doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


def format_sources(docs: Iterable[KnowledgeDoc]) -> List[dict]:
    seen = set()
    sources: List[dict] = []
    for doc in docs:
        key = (doc.source_id, doc.section)
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "source_id": doc.source_id,
                "title": doc.title,
                "section": doc.section,
                "source_file": doc.source_file,
            }
        )
    return sources
