from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence
import re


@dataclass(frozen=True)
class KnowledgeDoc:
    source_id: str
    title: str
    section: str
    roles: tuple[str, ...]
    stacks: tuple[str, ...]
    content: str


KNOWLEDGE_BASE: tuple[KnowledgeDoc, ...] = (
    KnowledgeDoc(
        source_id="ENG-SETUP-001",
        title="Engineering Environment Setup",
        section="Local Development Baseline",
        roles=("backend", "frontend", "devops"),
        stacks=("python", "node", "java", "go"),
        content=(
            "Install Node.js 20+, Python 3.11+, and Docker Desktop. Clone repositories, copy .env templates, "
            "run docker compose up --build, and verify services at localhost ports 3000, 8000, and 8001."
        ),
    ),
    KnowledgeDoc(
        source_id="ENG-SETUP-002",
        title="Backend Service Setup",
        section="API Service Bootstrapping",
        roles=("backend",),
        stacks=("python", "java", "node"),
        content=(
            "Backend developers should install dependencies with pip install -r requirements.txt, run alembic upgrade head, "
            "and start FastAPI with uvicorn app.main:app --reload. Validate health at /health and docs at /docs."
        ),
    ),
    KnowledgeDoc(
        source_id="ENG-SETUP-003",
        title="Frontend Service Setup",
        section="UI Service Bootstrapping",
        roles=("frontend",),
        stacks=("node",),
        content=(
            "Frontend developers run npm ci, then npm run dev inside /frontend. Use NEXT_PUBLIC_API_URL to point to backend. "
            "Validate UI at localhost:3000 and lint with npm run lint before opening pull requests."
        ),
    ),
    KnowledgeDoc(
        source_id="ENG-SETUP-004",
        title="DevOps Setup Standards",
        section="Infrastructure Toolchain",
        roles=("devops",),
        stacks=("python", "go", "java", "node"),
        content=(
            "DevOps onboarding requires kubectl, helm, and terraform setup. Request cloud sandbox access via Jira template ONB-REQ, "
            "configure read-only production dashboards, and validate CI workflows in GitHub Actions."
        ),
    ),
    KnowledgeDoc(
        source_id="SEC-POL-001",
        title="Security and Compliance Policy",
        section="Mandatory Security Tasks",
        roles=("backend", "frontend", "devops"),
        stacks=("python", "node", "java", "go"),
        content=(
            "All engineers must complete secure coding training, enable MFA on GitHub and Slack, and review incident escalation runbooks "
            "within the first onboarding week. Compliance is required before production permissions are granted."
        ),
    ),
    KnowledgeDoc(
        source_id="ARCH-STD-001",
        title="Platform Architecture Overview",
        section="Service Boundaries",
        roles=("backend", "frontend", "devops"),
        stacks=("python", "node", "java", "go"),
        content=(
            "The platform uses Next.js frontend, FastAPI backend, and an agent service. PostgreSQL stores transactional data, "
            "Redis supports cache and pub-sub, and pgvector supports semantic retrieval for internal knowledge queries."
        ),
    ),
    KnowledgeDoc(
        source_id="OPS-PROC-001",
        title="Internal Process Playbook",
        section="Communication and Delivery",
        roles=("backend", "frontend", "devops"),
        stacks=("python", "node", "java", "go"),
        content=(
            "New hires join #engineering-onboarding in Slack, attend architecture walkthroughs, and follow Jira workflow rules: "
            "backlog refinement, active development, code review, and done after QA validation."
        ),
    ),
)

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


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in STOPWORDS and len(token) > 2
    }


def retrieve_documents(
    query: str,
    role: str | None = None,
    stacks: Sequence[str] | None = None,
    top_k: int = 3,
) -> list[KnowledgeDoc]:
    """
    Lightweight lexical retrieval that prioritizes role and stack matches.
    This keeps responses grounded in the known document set.
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    stack_set = {s.lower() for s in (stacks or [])}
    scored: list[tuple[float, KnowledgeDoc]] = []

    for doc in KNOWLEDGE_BASE:
        doc_tokens = _tokenize(doc.content + " " + doc.title + " " + doc.section)
        overlap = len(query_tokens & doc_tokens)
        if overlap == 0:
            continue

        score = float(overlap)
        if role and role.lower() in doc.roles:
            score += 1.0
        if stack_set and stack_set.intersection(doc.stacks):
            score += 0.5

        scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


def format_sources(docs: Iterable[KnowledgeDoc]) -> list[dict[str, str]]:
    return [
        {
            "source_id": doc.source_id,
            "title": doc.title,
            "section": doc.section,
        }
        for doc in docs
    ]
