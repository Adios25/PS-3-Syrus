from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
import re

from knowledge_base import format_sources, retrieve_documents

Role = Literal["backend", "frontend", "devops"]
ExperienceLevel = Literal["intern", "junior", "senior"]
Status = Literal["in_progress", "completed"]

ALLOWED_ROLES: tuple[Role, ...] = ("backend", "frontend", "devops")
ALLOWED_EXPERIENCE_LEVELS: tuple[ExperienceLevel, ...] = ("intern", "junior", "senior")
KNOWN_STACKS = {
    "python",
    "node",
    "java",
    "go",
    "rust",
    "typescript",
}


@dataclass
class Persona:
    name: str | None = None
    email: str | None = None
    team: str | None = None
    role: Role | None = None
    experience_level: ExperienceLevel | None = None
    tech_stack: list[str] = field(default_factory=list)

    def missing_fields(self) -> list[str]:
        missing: list[str] = []
        if not self.name:
            missing.append("name")
        if not self.role:
            missing.append("role")
        if not self.experience_level:
            missing.append("experience_level")
        if not self.tech_stack:
            missing.append("tech_stack")
        return missing


@dataclass
class ChecklistItem:
    item_id: int
    title: str
    description: str
    category: str
    source_refs: list[str]
    is_completed: bool = False


@dataclass
class CompletionEmail:
    to: str
    subject: str
    body: str
    payload: dict


@dataclass
class OnboardingSession:
    session_id: str
    persona: Persona
    checklist: list[ChecklistItem] = field(default_factory=list)
    status: Status = "in_progress"
    completion_email: CompletionEmail | None = None
    confidence_score: float | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    @property
    def completed_items(self) -> list[ChecklistItem]:
        return [item for item in self.checklist if item.is_completed]

    @property
    def pending_items(self) -> list[ChecklistItem]:
        return [item for item in self.checklist if not item.is_completed]

    @property
    def progress_percent(self) -> int:
        if not self.checklist:
            return 0
        completed = len(self.completed_items)
        return round((completed / len(self.checklist)) * 100)


class OnboardingOrchestrator:
    def __init__(self, hr_email: str = "hr@antigravity.example") -> None:
        self._sessions: dict[str, OnboardingSession] = {}
        self._hr_email = hr_email

    def create_session(self, persona_seed: Persona | None = None) -> OnboardingSession:
        session_id = uuid4().hex
        session = OnboardingSession(session_id=session_id, persona=persona_seed or Persona())
        self._sessions[session_id] = session
        self._maybe_initialize_checklist(session)
        return session

    def get_session(self, session_id: str) -> OnboardingSession | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[OnboardingSession]:
        return list(self._sessions.values())

    def update_profile(
        self,
        session_id: str,
        name: str | None = None,
        email: str | None = None,
        team: str | None = None,
        role: str | None = None,
        experience_level: str | None = None,
        tech_stack: list[str] | None = None,
    ) -> OnboardingSession:
        session = self._require_session(session_id)
        persona = session.persona

        if name:
            persona.name = name.strip()
        if email:
            persona.email = email.strip().lower()
        if team:
            persona.team = team.strip()
        if role and role.lower() in ALLOWED_ROLES:
            persona.role = role.lower()  # type: ignore[assignment]
        if experience_level and experience_level.lower() in ALLOWED_EXPERIENCE_LEVELS:
            persona.experience_level = experience_level.lower()  # type: ignore[assignment]
        if tech_stack:
            normalized = sorted({stack.lower() for stack in tech_stack if stack.lower() in KNOWN_STACKS})
            if normalized:
                persona.tech_stack = normalized

        self._maybe_initialize_checklist(session)
        session.touch()
        return session

    def mark_item(self, session_id: str, item_id: int, is_completed: bool) -> OnboardingSession:
        session = self._require_session(session_id)
        matched = next((item for item in session.checklist if item.item_id == item_id), None)
        if not matched:
            raise ValueError(f"Checklist item {item_id} not found")
        matched.is_completed = is_completed
        self._refresh_status(session)
        session.touch()
        return session

    def complete_onboarding(self, session_id: str) -> CompletionEmail:
        session = self._require_session(session_id)
        self._refresh_status(session)
        if session.pending_items:
            raise ValueError("Cannot complete onboarding with pending checklist items")

        email = self._build_completion_email(session)
        session.completion_email = email
        session.confidence_score = self._estimate_confidence(session)
        session.status = "completed"
        session.touch()
        return email

    def handle_chat(self, session_id: str, message: str) -> dict:
        session = self._require_session(session_id)
        message_clean = message.strip()
        if not message_clean:
            return self._response(
                session,
                "Please send a message so I can help with onboarding.",
                sources=[],
            )

        self._ingest_persona_from_text(session.persona, message_clean)
        self._maybe_initialize_checklist(session)

        if session.persona.missing_fields():
            prompt = self._next_profile_question(session.persona)
            session.touch()
            return self._response(session, prompt, sources=[])

        lower = message_clean.lower()

        completion_hit = re.search(r"\b(onboarding complete|finish onboarding|completed onboarding)\b", lower)
        if completion_hit:
            if session.pending_items:
                pending_titles = ", ".join(item.title for item in session.pending_items)
                return self._response(
                    session,
                    f"You still have pending tasks: {pending_titles}. Complete those first and ask me to finish onboarding again.",
                    sources=[],
                )
            email = self.complete_onboarding(session.session_id)
            return self._response(
                session,
                (
                    "Onboarding is now completed. I generated a structured HR completion report and queued it for delivery. "
                    "Use the completion panel to review the payload."
                ),
                sources=[],
                completion_email=email.payload,
            )

        mark_match = re.search(r"(?:mark|complete|done)\s*(?:task\s*)?#?(\d+)", lower)
        if mark_match:
            item_id = int(mark_match.group(1))
            try:
                updated_session = self.mark_item(session.session_id, item_id=item_id, is_completed=True)
            except ValueError:
                return self._response(
                    session,
                    f"I couldn't find task #{item_id}. Ask for your checklist to see valid task IDs.",
                    sources=[],
                )

            if not updated_session.pending_items:
                guidance = (
                    "All checklist tasks are complete. Say 'finish onboarding' and I will generate the HR completion email."
                )
            else:
                guidance = f"Task #{item_id} marked complete. Progress is {updated_session.progress_percent}%."
            return self._response(updated_session, guidance, sources=[])

        if re.search(r"\b(progress|status|checklist|tasks)\b", lower):
            checklist_lines = [
                f"#{item.item_id} [{'x' if item.is_completed else ' '}] {item.title}"
                for item in session.checklist
            ]
            summary = "\n".join(checklist_lines)
            return self._response(
                session,
                f"Current onboarding status: {session.status}, progress {session.progress_percent}%.\n{summary}",
                sources=[],
            )

        docs = retrieve_documents(
            query=message_clean,
            role=session.persona.role,
            stacks=session.persona.tech_stack,
            top_k=3,
        )
        if not docs:
            return self._response(
                session,
                (
                    "I can only answer using the structured onboarding knowledge base, and I could not find a matching source for that request. "
                    "Ask about setup, architecture, security, Jira workflow, or onboarding tasks."
                ),
                sources=[],
            )

        answer_fragments = [doc.content for doc in docs[:2]]
        response_text = " ".join(answer_fragments)
        session.touch()
        return self._response(
            session,
            f"Based on internal docs: {response_text}",
            sources=format_sources(docs),
        )

    def _response(
        self,
        session: OnboardingSession,
        message: str,
        sources: list[dict],
        completion_email: dict | None = None,
    ) -> dict:
        return {
            "session_id": session.session_id,
            "message": message,
            "sources": sources,
            "status": session.status,
            "progress_percent": session.progress_percent,
            "checklist": [self._serialize_item(item) for item in session.checklist],
            "missing_profile_fields": session.persona.missing_fields(),
            "completion_email": completion_email,
            "profile": self._serialize_profile(session.persona),
        }

    def _serialize_item(self, item: ChecklistItem) -> dict:
        return {
            "item_id": item.item_id,
            "title": item.title,
            "description": item.description,
            "category": item.category,
            "source_refs": item.source_refs,
            "is_completed": item.is_completed,
        }

    def _serialize_profile(self, persona: Persona) -> dict:
        return {
            "name": persona.name,
            "email": persona.email,
            "team": persona.team,
            "role": persona.role,
            "experience_level": persona.experience_level,
            "tech_stack": persona.tech_stack,
        }

    def _require_session(self, session_id: str) -> OnboardingSession:
        session = self.get_session(session_id)
        if session is None:
            raise ValueError("Session not found")
        return session

    def _refresh_status(self, session: OnboardingSession) -> None:
        session.status = "completed" if session.checklist and not session.pending_items else "in_progress"

    def _maybe_initialize_checklist(self, session: OnboardingSession) -> None:
        if session.checklist:
            return
        persona = session.persona
        if persona.missing_fields():
            return
        session.checklist = self._build_checklist(persona)
        session.touch()

    def _next_profile_question(self, persona: Persona) -> str:
        missing = persona.missing_fields()
        if not missing:
            return "Your onboarding profile is complete. Ask any onboarding question or request checklist status."

        next_field = missing[0]
        if next_field == "name":
            return "What is your name?"
        if next_field == "role":
            return "What is your role: Backend, Frontend, or DevOps?"
        if next_field == "experience_level":
            return "What is your experience level: Intern, Junior, or Senior?"
        if next_field == "tech_stack":
            return "What is your primary tech stack (for example: Python, Node, Java, or Go)?"
        return "Please provide the missing onboarding profile fields."

    def _ingest_persona_from_text(self, persona: Persona, text: str) -> None:
        lower = text.lower()

        name_match = re.search(r"(?:my name is|i am|i'm)\s+([a-zA-Z][a-zA-Z\s'-]{1,40})", text, re.IGNORECASE)
        if name_match and not persona.name:
            candidate = name_match.group(1).strip().split(" ")[0:2]
            persona.name = " ".join(candidate).strip().title()

        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        if email_match and not persona.email:
            persona.email = email_match.group(0).lower()

        team_match = re.search(r"team\s*(?:is|:)?\s*([a-zA-Z][a-zA-Z\s-]{1,30})", text, re.IGNORECASE)
        if team_match and not persona.team:
            persona.team = team_match.group(1).strip().title()

        for role in ALLOWED_ROLES:
            if role in lower:
                persona.role = role
                break

        for level in ALLOWED_EXPERIENCE_LEVELS:
            if level in lower:
                persona.experience_level = level
                break

        mentioned_stacks = {stack for stack in KNOWN_STACKS if stack in lower}
        if mentioned_stacks:
            persona.tech_stack = sorted(set(persona.tech_stack).union(mentioned_stacks))

    def _build_checklist(self, persona: Persona) -> list[ChecklistItem]:
        role = persona.role or "backend"
        level = persona.experience_level or "junior"
        primary_stack = persona.tech_stack[0] if persona.tech_stack else "python"

        base_tasks = [
            (
                "Complete account security setup",
                "Enable MFA on GitHub and Slack and review incident escalation contacts.",
                "compliance",
                ["SEC-POL-001"],
            ),
            (
                "Set up local engineering environment",
                "Install required language runtimes and boot core services with Docker Compose.",
                "environment",
                ["ENG-SETUP-001"],
            ),
            (
                "Review platform architecture",
                "Read service-boundary documentation and identify where your team contributes.",
                "architecture",
                ["ARCH-STD-001"],
            ),
            (
                "Join onboarding communication channels",
                "Join #engineering-onboarding and confirm Jira workflow expectations.",
                "process",
                ["OPS-PROC-001"],
            ),
        ]

        role_specific = {
            "backend": (
                "Provision backend developer environment",
                "Install backend dependencies, run migrations, and verify API health endpoints.",
                "role_setup",
                ["ENG-SETUP-002"],
            ),
            "frontend": (
                "Provision frontend developer environment",
                "Install frontend dependencies, run dev server, and validate lint/build workflow.",
                "role_setup",
                ["ENG-SETUP-003"],
            ),
            "devops": (
                "Provision infrastructure operations environment",
                "Configure kubectl, helm, terraform, and validate pipeline observability access.",
                "role_setup",
                ["ENG-SETUP-004"],
            ),
        }

        level_specific = {
            "intern": (
                "Complete intern mentor kickoff",
                "Schedule onboarding sync with mentor and document first-week goals.",
                "career",
                ["OPS-PROC-001"],
            ),
            "junior": (
                "Shadow code review workflow",
                "Observe at least one pull-request review cycle and capture process notes.",
                "career",
                ["OPS-PROC-001"],
            ),
            "senior": (
                "Review ownership and escalation model",
                "Align with engineering manager on incident ownership expectations.",
                "career",
                ["SEC-POL-001", "OPS-PROC-001"],
            ),
        }

        stack_task = (
            f"Validate {primary_stack.title()} development workflow",
            f"Run a minimal {primary_stack.title()} service task and document any setup blockers.",
            "tech_stack",
            ["ENG-SETUP-001"],
        )

        selected_tasks = base_tasks + [role_specific[role], level_specific[level], stack_task]
        checklist: list[ChecklistItem] = []
        for idx, task in enumerate(selected_tasks, start=1):
            title, description, category, refs = task
            checklist.append(
                ChecklistItem(
                    item_id=idx,
                    title=title,
                    description=description,
                    category=category,
                    source_refs=list(refs),
                )
            )
        return checklist

    def _estimate_confidence(self, session: OnboardingSession) -> float:
        if not session.checklist:
            return 0.5
        source_coverage = sum(1 for item in session.checklist if item.source_refs) / len(session.checklist)
        profile_completeness = 1.0 - (len(session.persona.missing_fields()) / 4)
        confidence = round((0.65 * source_coverage) + (0.35 * profile_completeness), 2)
        return min(max(confidence, 0.0), 1.0)

    def _build_completion_email(self, session: OnboardingSession) -> CompletionEmail:
        completed_titles = [item.title for item in session.completed_items]
        pending_titles = [item.title for item in session.pending_items]
        timestamp = datetime.now(timezone.utc).isoformat()

        payload = {
            "to": self._hr_email,
            "subject": f"Onboarding Completed: {session.persona.name or 'New Hire'}",
            "employee": {
                "name": session.persona.name,
                "email": session.persona.email,
                "role": session.persona.role,
                "team": session.persona.team,
                "experience_level": session.persona.experience_level,
                "tech_stack": session.persona.tech_stack,
            },
            "summary": {
                "status": "Completed",
                "completed_items": completed_titles,
                "pending_items": pending_titles,
                "completion_timestamp_utc": timestamp,
            },
            "confidence_score": self._estimate_confidence(session),
            "delivery_status": "sent",
        }

        body = (
            "Hello HR Team,\n\n"
            f"Employee: {session.persona.name or 'N/A'}\n"
            f"Role/Team: {session.persona.role or 'N/A'} / {session.persona.team or 'N/A'}\n"
            f"Experience Level: {session.persona.experience_level or 'N/A'}\n"
            f"Tech Stack: {', '.join(session.persona.tech_stack) if session.persona.tech_stack else 'N/A'}\n"
            f"Completion Timestamp (UTC): {timestamp}\n"
            f"Completed Items: {len(completed_titles)}\n"
            f"Pending Items: {len(pending_titles)}\n"
            f"Confidence Score: {payload['confidence_score']}\n\n"
            "Regards,\n"
            "PS-03 Autonomous Onboarding Agent"
        )
        return CompletionEmail(
            to=self._hr_email,
            subject=payload["subject"],
            body=body,
            payload=payload,
        )
