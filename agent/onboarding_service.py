from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Sequence, Tuple
from uuid import uuid4
import re

from knowledge_base import format_sources, retrieve_documents
from workflow_assets import (
    ChecklistTemplateItem,
    PersonaTemplate,
    StarterTicket,
    load_checklist_templates,
    load_completion_template,
    load_persona_templates,
    select_checklist_section,
    select_starter_ticket,
)

Role = Literal["backend", "frontend", "devops", "fullstack"]
ExperienceLevel = Literal["intern", "junior", "senior"]
Status = Literal["in_progress", "completed"]

ALLOWED_ROLES: Tuple[Role, ...] = ("backend", "frontend", "devops", "fullstack")
ALLOWED_EXPERIENCE_LEVELS: Tuple[ExperienceLevel, ...] = ("intern", "junior", "senior")
KNOWN_STACKS = {
    "python",
    "node",
    "node.js",
    "java",
    "go",
    "react",
    "typescript",
    "aws",
    "kubernetes",
    "terraform",
    "fastapi",
}


@dataclass
class Persona:
    name: Optional[str] = None
    email: Optional[str] = None
    team: Optional[str] = None
    role: Optional[Role] = None
    experience_level: Optional[ExperienceLevel] = None
    tech_stack: List[str] = field(default_factory=list)

    employee_id: Optional[str] = None
    department: Optional[str] = None
    manager_name: Optional[str] = None
    manager_email: Optional[str] = None
    mentor_name: Optional[str] = None
    mentor_email: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    matched_persona_name: Optional[str] = None

    def missing_fields(self) -> List[str]:
        missing: List[str] = []
        if not self.name:
            missing.append("name")
        if not self.role:
            missing.append("role")
        if not self.experience_level:
            missing.append("experience_level")
        if not self.tech_stack:
            missing.append("tech_stack")
        if not self.team:
            missing.append("team")
        return missing


@dataclass
class ChecklistItem:
    item_id: int
    checklist_code: str
    title: str
    description: str
    category: str
    owner: str
    deadline: str
    source_refs: List[str]
    is_completed: bool = False
    completed_at: Optional[str] = None


@dataclass
class CompletionEmail:
    to: List[str]
    subject: str
    body: str
    payload: Dict


@dataclass
class MCPActionResult:
    tool_name: str
    status: str
    payload: Dict


@dataclass
class GeneratedFAQ:
    question: str
    answer: str
    source_ids: List[str]
    created_at: str


@dataclass
class OnboardingSession:
    session_id: str
    persona: Persona
    checklist: List[ChecklistItem] = field(default_factory=list)
    status: Status = "in_progress"
    completion_email: Optional[CompletionEmail] = None
    confidence_score: Optional[float] = None
    assigned_ticket: Optional[StarterTicket] = None
    checklist_source_section: Optional[str] = None
    inference_notes: List[str] = field(default_factory=list)
    mcp_actions: List[MCPActionResult] = field(default_factory=list)
    generated_faqs: List[GeneratedFAQ] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    @property
    def completed_items(self) -> List[ChecklistItem]:
        return [item for item in self.checklist if item.is_completed]

    @property
    def pending_items(self) -> List[ChecklistItem]:
        return [item for item in self.checklist if not item.is_completed]

    @property
    def progress_percent(self) -> int:
        if not self.checklist:
            return 0
        completed = len(self.completed_items)
        return round((completed / len(self.checklist)) * 100)


class OnboardingOrchestrator:
    def __init__(self, hr_email: str = "hr@novabyte.dev") -> None:
        self._sessions: Dict[str, OnboardingSession] = {}
        self._hr_email = hr_email
        self._persona_templates = load_persona_templates()
        self._checklist_templates = load_checklist_templates()
        self._completion_template = load_completion_template()

    def create_session(self, persona_seed: Optional[Persona] = None) -> OnboardingSession:
        session_id = uuid4().hex
        session = OnboardingSession(session_id=session_id, persona=persona_seed or Persona())
        self._sessions[session_id] = session
        self._apply_dataset_persona(session)
        self._maybe_initialize_checklist(session)
        return session

    def get_session(self, session_id: str) -> Optional[OnboardingSession]:
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[OnboardingSession]:
        return list(self._sessions.values())

    def update_profile(
        self,
        session_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        team: Optional[str] = None,
        role: Optional[str] = None,
        experience_level: Optional[str] = None,
        tech_stack: Optional[List[str]] = None,
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
            normalized = self._normalize_stack_list(tech_stack)
            if normalized:
                persona.tech_stack = normalized

        self._apply_dataset_persona(session)
        self._maybe_initialize_checklist(session)
        session.touch()
        return session

    def mark_item(self, session_id: str, item_id: int, is_completed: bool) -> OnboardingSession:
        session = self._require_session(session_id)
        matched = next((item for item in session.checklist if item.item_id == item_id), None)
        if not matched:
            raise ValueError(f"Checklist item {item_id} not found")

        matched.is_completed = is_completed
        matched.completed_at = datetime.now(timezone.utc).isoformat() if is_completed else None
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

    def handle_chat(self, session_id: str, message: str) -> Dict:
        session = self._require_session(session_id)
        message_clean = message.strip()
        if not message_clean:
            return self._response(
                session,
                "Please send a message so I can guide your onboarding.",
                sources=[],
            )

        had_checklist = bool(session.checklist)

        self._ingest_persona_from_text(session.persona, message_clean)
        self._apply_dataset_persona(session)
        self._maybe_initialize_checklist(session)

        if session.persona.missing_fields():
            prompt = self._next_profile_question(session.persona)
            session.touch()
            return self._response(session, prompt, sources=[])

        if not had_checklist and session.checklist:
            response_message = self._initial_path_message(session)
            session.touch()
            return self._response(session, response_message, sources=[{"source_id": "KB-007", "title": "NovaByte Technologies — Onboarding Checklists", "section": session.checklist_source_section, "source_file": "onboarding_checklists.md"}])

        lower = message_clean.lower()

        completion_hit = re.search(r"\b(onboarding complete|finish onboarding|completed onboarding|finalize onboarding)\b", lower)
        if completion_hit:
            if session.pending_items:
                pending_codes = ", ".join(item.checklist_code for item in session.pending_items[:6])
                return self._response(
                    session,
                    f"Onboarding is still in progress. Pending checklist items include: {pending_codes}. Complete them first, then ask me to finish onboarding.",
                    sources=[{"source_id": "KB-007", "title": "NovaByte Technologies — Onboarding Checklists", "section": session.checklist_source_section or "Checklist", "source_file": "onboarding_checklists.md"}],
                )
            email = self.complete_onboarding(session.session_id)
            return self._response(
                session,
                "Onboarding completed. I generated the structured HR completion report using KB-009 Template 1 fields.",
                sources=[{"source_id": "KB-009", "title": "NovaByte Technologies — HR Email Templates", "section": "Template 1: Onboarding Completion Notification", "source_file": "email_templates.md"}],
                completion_email=email.payload,
            )

        if re.search(r"\b(first task|starter ticket|jira ticket|ticket)\b", lower):
            ticket = session.assigned_ticket or self._assign_starter_ticket(session)
            if not ticket:
                return self._response(
                    session,
                    "I could not find a starter ticket for this profile in KB-010 yet.",
                    sources=[{"source_id": "KB-010", "title": "NovaByte Technologies — Starter Tickets for New Employees", "section": "Overview", "source_file": "starter_tickets.md"}],
                )

            criteria = "\n".join([f"- {item}" for item in ticket.acceptance_criteria[:4]])
            return self._response(
                session,
                (
                    f"Assigned starter ticket: {ticket.ticket_id} — {ticket.title}\n"
                    f"Project: {ticket.project}\nPriority: {ticket.priority}\nRepository: {ticket.repository}\n"
                    f"Acceptance Criteria:\n{criteria}"
                ),
                sources=[{"source_id": "KB-010", "title": "NovaByte Technologies — Starter Tickets for New Employees", "section": ticket.section, "source_file": "starter_tickets.md"}],
            )

        if re.search(r"\b(next step|what next|what should i do next)\b", lower):
            next_item = session.pending_items[0] if session.pending_items else None
            if not next_item:
                return self._response(
                    session,
                    "All checklist items are complete. Ask me to finish onboarding and generate the HR completion email.",
                    sources=[],
                )
            return self._response(
                session,
                (
                    f"Next checklist step is {next_item.checklist_code}: {next_item.title}. "
                    f"Owner: {next_item.owner}. Deadline: {next_item.deadline}."
                ),
                sources=[{"source_id": "KB-007", "title": "NovaByte Technologies — Onboarding Checklists", "section": next_item.category, "source_file": "onboarding_checklists.md"}],
            )

        if re.search(r"\b(example workflow|workflow example|personalized flow|onboarding flow)\b", lower):
            return self._response(
                session,
                self._build_example_flow_message(session),
                sources=[
                    {"source_id": "KB-007", "title": "NovaByte Technologies — Onboarding Checklists", "section": session.checklist_source_section or "Checklist", "source_file": "onboarding_checklists.md"},
                    {"source_id": "KB-003", "title": "NovaByte Technologies — System Architecture Documentation", "section": "Frontend Architecture", "source_file": "architecture_documentation.md"},
                    {"source_id": "KB-002", "title": "NovaByte Technologies — Engineering Standards & Guidelines", "section": "3. Pull Request (PR) Guidelines", "source_file": "engineering_standards.md"},
                ],
            )

        mark_result = self._try_mark_done(session, message_clean)
        if mark_result:
            return mark_result

        if re.search(r"\b(progress|status|checklist|tasks)\b", lower):
            checklist_lines = [
                f"{item.checklist_code} [{'x' if item.is_completed else ' '}] {item.title}"
                for item in session.checklist[:20]
            ]
            summary = "\n".join(checklist_lines)
            return self._response(
                session,
                f"Status: {session.status}. Progress: {session.progress_percent}%.\n{summary}",
                sources=[{"source_id": "KB-007", "title": "NovaByte Technologies — Onboarding Checklists", "section": session.checklist_source_section or "Checklist", "source_file": "onboarding_checklists.md"}],
            )

        integration_result = self._handle_integration_actions(session, message_clean)
        if integration_result:
            return integration_result

        env_result = self._handle_environment_verification(session, message_clean)
        if env_result:
            return env_result

        faq_result = self._handle_generated_faq_queries(session, message_clean)
        if faq_result:
            return faq_result

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
                    "I only answer from the PS03 structured knowledge base and couldn't find a matching source. "
                    "Ask about setup guides, standards, architecture, policies, org contacts, or onboarding FAQ."
                ),
                sources=[],
            )

        answer_fragments = [doc.content[:420].strip() for doc in docs[:2]]
        response_text = " ".join(answer_fragments)
        self._capture_generated_faq(
            session=session,
            question=message_clean,
            answer=response_text,
            source_ids=[doc.source_id for doc in docs],
        )
        session.touch()
        return self._response(
            session,
            f"Based on official onboarding docs: {response_text}",
            sources=format_sources(docs),
        )

    def _initial_path_message(self, session: OnboardingSession) -> str:
        first_step = session.pending_items[0] if session.pending_items else None
        inference = f" Note: {session.inference_notes[-1]}" if session.inference_notes else ""
        ticket_text = ""
        if session.assigned_ticket:
            ticket_text = (
                f" Starter ticket from KB-010 is pre-selected: {session.assigned_ticket.ticket_id} "
                f"({session.assigned_ticket.title})."
            )

        if session.persona.role == "backend" and session.persona.experience_level == "intern" and "node" in session.persona.tech_stack:
            return (
                "Onboarding path ready for Backend Intern (Node.js). "
                "Sequence: BI-01 Install Node.js 20, BI-05 Clone connector-runtime, BI-09 Start service locally, "
                "BI-11 Review backend architecture (KB-003), BI-12 Read API standards (KB-002), BI-18 Complete starter bug fix."
                f"{ticket_text}{inference}"
            )

        if session.persona.role == "frontend" and session.persona.experience_level == "senior" and "react" in session.persona.tech_stack:
            return (
                "Onboarding path ready for Frontend Senior (React). "
                "Sequence: review frontend architecture (KB-003), access design system and Storybook, "
                "understand deployment pipeline (KB-002/KB-003), review PR guidelines (KB-002), then pick a starter ticket."
                f"{ticket_text}{inference}"
            )

        return (
            f"Onboarding path ready using KB-007 section '{session.checklist_source_section}'."
            f" Your first step is {first_step.checklist_code if first_step else 'N/A'}: {first_step.title if first_step else 'N/A'}."
            f"{ticket_text}{inference}"
        )

    def _build_example_flow_message(self, session: OnboardingSession) -> str:
        persona = session.persona
        if persona.role == "backend" and persona.experience_level == "intern" and "node" in persona.tech_stack:
            return (
                "Backend Intern (Node.js) workflow: "
                "1) Set up Node environment (BI-01, BI-02, BI-03), "
                "2) Clone repo and configure env (BI-05, BI-06), "
                "3) Run local stack and tests (BI-07 to BI-10), "
                "4) Read backend architecture and API standards (BI-11, BI-12), "
                "5) Complete starter bug-fix ticket and PR (BI-18 to BI-20)."
            )

        if persona.role == "frontend" and "react" in persona.tech_stack:
            return (
                "Frontend Senior (React) workflow: "
                "1) Review frontend architecture (KB-003 Frontend section), "
                "2) Access design system and Storybook (@novabyte/ui-kit), "
                "3) Understand CI/CD deployment path (GitHub Actions -> ArgoCD), "
                "4) Review PR guidelines and review expectations (KB-002), "
                "5) Pick and ship first ticket with screenshots/tests."
            )

        first_pending = session.pending_items[0] if session.pending_items else None
        return (
            f"Personalized flow is active from '{session.checklist_source_section}'. "
            f"Current next step: {first_pending.checklist_code if first_pending else 'None'} "
            f"{first_pending.title if first_pending else ''}".strip()
        )

    def _execute_mcp_tool(self, tool_name: str, arguments: Dict) -> MCPActionResult:
        if tool_name == "provision_github_access":
            payload = {
                "status": "success",
                "message": f"Added user {arguments.get('username', 'new-hire')} to GitHub org.",
                "org": "novabyte",
            }
        elif tool_name == "invite_to_slack":
            payload = {
                "status": "success",
                "channel": arguments.get("channel", "#engineering-onboarding"),
                "message": f"Invited {arguments.get('email', 'new-hire@novabyte.dev')} to onboarding channel.",
            }
        elif tool_name == "assign_jira_ticket":
            payload = {
                "status": "success",
                "ticket_id": arguments.get("ticket_id", "ONB-001"),
                "message": "First-week ticket assigned.",
            }
        elif tool_name == "send_slack_welcome":
            payload = {
                "status": "success",
                "channel": arguments.get("channel", "#new-joiners"),
                "message": f"Welcome message posted for {arguments.get('name', 'new hire')}.",
            }
        else:
            payload = {"status": "error", "message": "Unknown tool."}

        result = MCPActionResult(tool_name=tool_name, status=payload["status"], payload=payload)
        return result

    def _handle_integration_actions(self, session: OnboardingSession, message: str) -> Optional[Dict]:
        lower = message.lower()
        if not re.search(r"\b(github|slack|jira|provision|invite|welcome)\b", lower):
            return None

        actions: List[MCPActionResult] = []
        persona = session.persona
        employee_email = persona.email or "new-hire@novabyte.dev"
        employee_name = persona.name or "New Hire"
        username = employee_email.split("@", 1)[0]

        if re.search(r"\b(all access|everything|all tools|provision)\b", lower):
            actions.append(self._execute_mcp_tool("provision_github_access", {"username": username}))
            actions.append(self._execute_mcp_tool("invite_to_slack", {"email": employee_email}))
            ticket_id = session.assigned_ticket.ticket_id if session.assigned_ticket else "ONB-001"
            actions.append(self._execute_mcp_tool("assign_jira_ticket", {"ticket_id": ticket_id}))
            actions.append(self._execute_mcp_tool("send_slack_welcome", {"name": employee_name}))
        else:
            if "github" in lower:
                actions.append(self._execute_mcp_tool("provision_github_access", {"username": username}))
            if "slack" in lower and "welcome" in lower:
                actions.append(self._execute_mcp_tool("send_slack_welcome", {"name": employee_name}))
            elif "slack" in lower:
                actions.append(self._execute_mcp_tool("invite_to_slack", {"email": employee_email}))
            if "jira" in lower or "ticket" in lower:
                ticket_id = session.assigned_ticket.ticket_id if session.assigned_ticket else "ONB-001"
                actions.append(self._execute_mcp_tool("assign_jira_ticket", {"ticket_id": ticket_id}))

        if not actions:
            return None

        session.mcp_actions.extend(actions)
        action_lines = [f"- {entry.tool_name}: {entry.payload.get('message', entry.status)}" for entry in actions]
        return self._response(
            session,
            "MCP actions executed (mocked):\n" + "\n".join(action_lines),
            sources=[{"source_id": "KB-011", "title": "NovaByte Technologies — Onboarding FAQ", "section": "Access & Accounts", "source_file": "onboarding_faq.md"}],
        )

    def _handle_environment_verification(self, session: OnboardingSession, message: str) -> Optional[Dict]:
        lower = message.lower()
        if not re.search(r"\b(verify environment|environment check|check my setup|local setup|env verification)\b", lower):
            return None

        env_items = [
            item
            for item in session.checklist
            if item.category in {"Environment Setup", "Verification"}
        ]
        if not env_items:
            return self._response(
                session,
                "No environment setup checklist exists yet for this session. Complete your profile first.",
                sources=[{"source_id": "KB-007", "title": "NovaByte Technologies — Onboarding Checklists", "section": "Common Checklist (All Roles & Levels)", "source_file": "onboarding_checklists.md"}],
            )

        pending = [item for item in env_items if not item.is_completed]
        if not pending:
            return self._response(
                session,
                "Environment verification passed. All setup and verification checklist items are completed.",
                sources=[{"source_id": "KB-007", "title": "NovaByte Technologies — Onboarding Checklists", "section": session.checklist_source_section or "Checklist", "source_file": "onboarding_checklists.md"}],
            )

        pending_codes = ", ".join(item.checklist_code for item in pending[:8])
        return self._response(
            session,
            f"Environment is not fully verified yet. Pending setup tasks: {pending_codes}.",
            sources=[{"source_id": "KB-007", "title": "NovaByte Technologies — Onboarding Checklists", "section": session.checklist_source_section or "Checklist", "source_file": "onboarding_checklists.md"}],
        )

    def _capture_generated_faq(self, session: OnboardingSession, question: str, answer: str, source_ids: List[str]) -> None:
        if not question.endswith("?"):
            return
        if len(session.generated_faqs) >= 20:
            return
        if any(entry.question.lower() == question.lower() for entry in session.generated_faqs):
            return

        entry = GeneratedFAQ(
            question=question,
            answer=answer[:500],
            source_ids=sorted(set(source_ids)),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        session.generated_faqs.append(entry)

    def _handle_generated_faq_queries(self, session: OnboardingSession, message: str) -> Optional[Dict]:
        lower = message.lower()
        if not re.search(r"\b(faq|knowledge base update|new faq|generated faq)\b", lower):
            return None

        if not session.generated_faqs:
            return self._response(
                session,
                "No generated FAQs captured yet. Ask onboarding questions and I will store grounded Q&A entries.",
                sources=[{"source_id": "KB-011", "title": "NovaByte Technologies — Onboarding FAQ", "section": "General Onboarding", "source_file": "onboarding_faq.md"}],
            )

        lines = []
        for idx, faq in enumerate(session.generated_faqs[-5:], start=1):
            source_text = ", ".join(faq.source_ids)
            lines.append(f"{idx}. Q: {faq.question}\n   Sources: {source_text}")

        return self._response(
            session,
            "Generated onboarding FAQs captured in this session:\n" + "\n".join(lines),
            sources=[{"source_id": "KB-011", "title": "NovaByte Technologies — Onboarding FAQ", "section": "General Onboarding", "source_file": "onboarding_faq.md"}],
        )

    def _try_mark_done(self, session: OnboardingSession, message: str) -> Optional[Dict]:
        upper = message.upper()
        code_match = re.search(r"\b([A-Z]{1,5}-\d{2,4})\b", upper)

        target_item: Optional[ChecklistItem] = None
        if code_match:
            code = code_match.group(1)
            target_item = next((item for item in session.checklist if item.checklist_code.upper() == code), None)

        if not target_item:
            number_match = re.search(r"(?:#|task\s*)(\d{1,3})", message.lower())
            if number_match:
                item_id = int(number_match.group(1))
                target_item = next((item for item in session.checklist if item.item_id == item_id), None)

        if not target_item:
            return None

        target_item.is_completed = True
        target_item.completed_at = datetime.now(timezone.utc).isoformat()
        self._refresh_status(session)
        session.touch()

        if not session.pending_items:
            guidance = "All checklist items are complete. Ask me to finish onboarding so I can generate the HR report."
        else:
            guidance = (
                f"Marked {target_item.checklist_code} as complete. "
                f"Progress is now {session.progress_percent}% ({len(session.completed_items)}/{len(session.checklist)})."
            )

        return self._response(
            session,
            guidance,
            sources=[{"source_id": "KB-007", "title": "NovaByte Technologies — Onboarding Checklists", "section": target_item.category, "source_file": "onboarding_checklists.md"}],
        )

    def _response(
        self,
        session: OnboardingSession,
        message: str,
        sources: List[Dict],
        completion_email: Optional[Dict] = None,
    ) -> Dict:
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
            "assigned_ticket": self._serialize_ticket(session.assigned_ticket),
            "inference_notes": list(session.inference_notes),
            "mcp_actions": [
                {"tool_name": action.tool_name, "status": action.status, "payload": action.payload}
                for action in session.mcp_actions
            ],
            "generated_faqs": [
                {
                    "question": faq.question,
                    "answer": faq.answer,
                    "source_ids": faq.source_ids,
                    "created_at": faq.created_at,
                }
                for faq in session.generated_faqs
            ],
        }

    def _serialize_item(self, item: ChecklistItem) -> Dict:
        return {
            "item_id": item.item_id,
            "checklist_code": item.checklist_code,
            "title": item.title,
            "description": item.description,
            "category": item.category,
            "owner": item.owner,
            "deadline": item.deadline,
            "source_refs": item.source_refs,
            "is_completed": item.is_completed,
            "completed_at": item.completed_at,
        }

    def _serialize_profile(self, persona: Persona) -> Dict:
        return {
            "name": persona.name,
            "email": persona.email,
            "team": persona.team,
            "role": persona.role,
            "experience_level": persona.experience_level,
            "tech_stack": persona.tech_stack,
            "employee_id": persona.employee_id,
            "department": persona.department,
            "manager_name": persona.manager_name,
            "manager_email": persona.manager_email,
            "mentor_name": persona.mentor_name,
            "mentor_email": persona.mentor_email,
            "location": persona.location,
            "start_date": persona.start_date,
            "matched_persona_name": persona.matched_persona_name,
        }

    def _serialize_ticket(self, ticket: Optional[StarterTicket]) -> Optional[Dict]:
        if not ticket:
            return None
        return {
            "ticket_id": ticket.ticket_id,
            "title": ticket.title,
            "project": ticket.project,
            "issue_type": ticket.issue_type,
            "priority": ticket.priority,
            "story_points": ticket.story_points,
            "repository": ticket.repository,
            "description": ticket.description,
            "acceptance_criteria": list(ticket.acceptance_criteria),
            "section": ticket.section,
        }

    def serialize_ticket(self, ticket: Optional[StarterTicket]) -> Optional[Dict]:
        return self._serialize_ticket(ticket)

    def _require_session(self, session_id: str) -> OnboardingSession:
        session = self.get_session(session_id)
        if session is None:
            raise ValueError("Session not found")
        return session

    def _refresh_status(self, session: OnboardingSession) -> None:
        session.status = "completed" if session.checklist and not session.pending_items else "in_progress"

    def _normalize_stack_list(self, values: Sequence[str]) -> List[str]:
        normalized = set()
        for value in values:
            lower = value.strip().lower()
            if not lower:
                continue
            if lower in {"nodejs", "node.js", "javascript"}:
                normalized.add("node")
            elif lower in {"reactjs", "react.js"}:
                normalized.add("react")
            else:
                normalized.add(lower)
        return sorted([item for item in normalized if item in KNOWN_STACKS])

    def _next_profile_question(self, persona: Persona) -> str:
        missing = persona.missing_fields()
        if not missing:
            return "Your onboarding profile is complete. Ask for your next step or checklist status."

        next_field = missing[0]
        if next_field == "name":
            return "What is your full name?"
        if next_field == "role":
            return "What role are you joining as: Backend, Frontend, DevOps, or Full-Stack?"
        if next_field == "experience_level":
            return "What is your experience level: Intern, Junior, or Senior?"
        if next_field == "tech_stack":
            return "What is your primary tech stack (for example: Node.js, Python, React, Java, Go)?"
        if next_field == "team":
            return "Which team or squad are you joining?"
        return "Please provide the remaining onboarding profile details."

    def _ingest_persona_from_text(self, persona: Persona, text: str) -> None:
        lower = text.lower()

        name_match = re.search(r"(?:my name is|i am|i'm)\s+([a-zA-Z][a-zA-Z\s'-]{1,60})", text, re.IGNORECASE)
        if name_match and not persona.name:
            candidate = " ".join(name_match.group(1).strip().split(" ")[:3])
            persona.name = candidate.title()

        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        if email_match:
            persona.email = email_match.group(0).lower()

        team_match = re.search(r"(?:team|squad)\s*(?:is|:)?\s*([a-zA-Z][a-zA-Z\s-]{1,40})", text, re.IGNORECASE)
        if team_match and not persona.team:
            persona.team = team_match.group(1).strip().title()

        role_markers = {
            "backend": ["backend"],
            "frontend": ["frontend", "react"],
            "devops": ["devops", "platform", "infra"],
            "fullstack": ["full-stack", "full stack"],
        }

        detected_roles: List[str] = []
        for role, markers in role_markers.items():
            if any(marker in lower for marker in markers):
                detected_roles.append(role)

        if "backend" in detected_roles and "frontend" in detected_roles:
            persona.role = "fullstack"
        elif detected_roles:
            persona.role = detected_roles[0]  # type: ignore[assignment]

        for level in ALLOWED_EXPERIENCE_LEVELS:
            if level in lower:
                persona.experience_level = level
                break

        stack_tokens = set(persona.tech_stack)
        if re.search(r"\bnode(\.js|js)?\b", lower):
            stack_tokens.add("node")
        if "python" in lower:
            stack_tokens.add("python")
        if "java" in lower:
            stack_tokens.add("java")
        if "go" in lower:
            stack_tokens.add("go")
        if "react" in lower:
            stack_tokens.add("react")
        if "typescript" in lower:
            stack_tokens.add("typescript")
        if "aws" in lower:
            stack_tokens.add("aws")
        if "kubernetes" in lower or "k8s" in lower:
            stack_tokens.add("kubernetes")

        persona.tech_stack = sorted(item for item in stack_tokens if item in KNOWN_STACKS)

    def _match_persona_template(self, persona: Persona) -> Optional[PersonaTemplate]:
        best_template: Optional[PersonaTemplate] = None
        best_score = -1.0

        for template in self._persona_templates:
            score = 0.0
            if persona.role and template.role == persona.role:
                score += 3.0
            if persona.experience_level and template.experience_level == persona.experience_level:
                score += 3.0
            if persona.tech_stack:
                overlap = len(set(persona.tech_stack).intersection(set(template.tech_stack)))
                score += overlap * 1.5
            if persona.name and template.profile_name.lower() in persona.name.lower():
                score += 4.0

            if score > best_score:
                best_score = score
                best_template = template

        if best_template and best_score >= 3.0:
            return best_template
        return None

    def _apply_dataset_persona(self, session: OnboardingSession) -> None:
        persona = session.persona
        template = self._match_persona_template(persona)
        if not template:
            return

        persona.employee_id = persona.employee_id or template.employee_id
        persona.department = persona.department or template.department
        persona.team = persona.team or template.team
        persona.manager_name = persona.manager_name or template.manager_name
        persona.manager_email = persona.manager_email or template.manager_email
        persona.mentor_name = persona.mentor_name or template.mentor_name
        persona.mentor_email = persona.mentor_email or template.mentor_email
        persona.location = persona.location or template.location
        persona.start_date = persona.start_date or template.start_date
        persona.email = persona.email or template.email
        persona.matched_persona_name = template.profile_name

        if not persona.role:
            persona.role = template.role  # type: ignore[assignment]
        if not persona.experience_level:
            persona.experience_level = template.experience_level  # type: ignore[assignment]
        if not persona.tech_stack:
            persona.tech_stack = list(template.tech_stack)

    def _maybe_initialize_checklist(self, session: OnboardingSession) -> None:
        if session.checklist:
            return

        persona = session.persona
        if persona.missing_fields():
            return

        common = self._checklist_templates.get("Common Checklist (All Roles & Levels)", tuple())
        section, note = select_checklist_section(
            role=persona.role or "backend",
            experience_level=persona.experience_level or "junior",
            tech_stack=persona.tech_stack,
        )
        specific = self._checklist_templates.get(section, tuple())

        if note:
            session.inference_notes.append(note)

        merged_templates: List[ChecklistTemplateItem] = list(common) + list(specific)

        checklist: List[ChecklistItem] = []
        for idx, template_item in enumerate(merged_templates, start=1):
            checklist.append(
                ChecklistItem(
                    item_id=idx,
                    checklist_code=template_item.code,
                    title=template_item.task,
                    description=(
                        f"Category: {template_item.category}. Owner: {template_item.owner}. "
                        f"Deadline: {template_item.deadline}."
                    ),
                    category=template_item.category,
                    owner=template_item.owner,
                    deadline=template_item.deadline,
                    source_refs=["KB-007", template_item.section],
                )
            )

        session.checklist = checklist
        session.checklist_source_section = section
        session.assigned_ticket = self._assign_starter_ticket(session)
        session.touch()

    def _assign_starter_ticket(self, session: OnboardingSession) -> Optional[StarterTicket]:
        if session.assigned_ticket:
            return session.assigned_ticket
        persona = session.persona
        if not persona.role or not persona.experience_level:
            return None

        ticket = select_starter_ticket(
            role=persona.role,
            experience_level=persona.experience_level,
            tech_stack=persona.tech_stack,
        )
        session.assigned_ticket = ticket
        return ticket

    def _estimate_confidence(self, session: OnboardingSession) -> float:
        if not session.checklist:
            return 0.5

        completion_ratio = len(session.completed_items) / len(session.checklist)

        compliance_codes = {"C-14", "C-15", "C-16", "C-17", "C-18", "C-19", "C-20", "C-21", "C-22"}
        compliance_items = [item for item in session.checklist if item.checklist_code in compliance_codes]
        if compliance_items:
            compliance_ratio = len([item for item in compliance_items if item.is_completed]) / len(compliance_items)
        else:
            compliance_ratio = 1.0

        profile_completeness = 1.0 - (len(session.persona.missing_fields()) / 5)
        confidence = round((0.5 * completion_ratio) + (0.3 * compliance_ratio) + (0.2 * profile_completeness), 2)
        return max(0.0, min(1.0, confidence))

    def _task_status_for_first_ticket(self, session: OnboardingSession) -> str:
        has_pickup = any("Pick up starter ticket" in item.title and item.is_completed for item in session.checklist)
        has_submit = any("Submit PR" in item.title and item.is_completed for item in session.checklist)
        has_merge = any(("PR approved and merged" in item.title or "get pr merged" in item.title.lower()) and item.is_completed for item in session.checklist)

        if has_merge:
            return "PR Merged"
        if has_submit:
            return "PR Submitted"
        if has_pickup:
            return "In Progress"
        return "Not Started"

    def _build_completion_email(self, session: OnboardingSession) -> CompletionEmail:
        completion_time = datetime.now(timezone.utc)
        completed_items = session.completed_items
        pending_items = session.pending_items
        total_tasks = len(session.checklist)
        completed_count = len(completed_items)
        pending_count = len(pending_items)
        completed_percentage = round((completed_count / total_tasks) * 100) if total_tasks else 0

        business_days = max((completion_time.date() - session.created_at.date()).days + 1, 1)

        compliance_codes = {
            "Security Awareness Training": "C-14",
            "Data Privacy & GDPR Training": "C-15",
            "Code of Conduct Training": "C-16",
            "Anti-Harassment Training": "C-17",
            "Insider Threat Awareness": "C-18",
            "Employee Handbook Signed": "C-19",
            "NDA Signed": "C-20",
            "Acceptable Use Policy Signed": "C-21",
            "IP Assignment Agreement Signed": "C-22",
        }

        code_to_item = {item.checklist_code: item for item in session.checklist}
        compliance_status = {}
        for label, code in compliance_codes.items():
            item = code_to_item.get(code)
            if not item:
                compliance_status[label] = "N/A"
            elif "Signed" in label:
                compliance_status[label] = "YES" if item.is_completed else "NO"
            else:
                compliance_status[label] = "COMPLETED" if item.is_completed else "PENDING"

        access_codes = {
            "GitHub (novabyte org)": "C-07",
            "Jira": "C-08",
            "Slack": "C-03",
            "Notion": "C-09",
            "VPN (WireGuard)": "C-10",
        }

        access_provisioned = {}
        for label, code in access_codes.items():
            item = code_to_item.get(code)
            access_provisioned[label] = "ACTIVE" if item and item.is_completed else "PENDING"

        if session.persona.role == "devops":
            access_provisioned["AWS Console (if applicable)"] = "PENDING"
        else:
            access_provisioned["AWS Console (if applicable)"] = "N/A"

        ticket = session.assigned_ticket
        ticket_title = ticket.title if ticket else "Not Assigned"
        ticket_id = ticket.ticket_id if ticket else "N/A"

        confidence = self._estimate_confidence(session)
        report_id = uuid4().hex

        payload = {
            "to": [self._hr_email, session.persona.manager_email or "manager@novabyte.dev"],
            "cc": [session.persona.email or "employee@novabyte.dev", session.persona.mentor_email or "mentor@novabyte.dev"],
            "from": "onboarding-agent@novabyte.dev",
            "subject": f"[Onboarding Complete] {session.persona.name or 'New Hire'} — {(session.persona.role or 'engineer').title()} | {session.persona.team or 'Engineering'}",
            "employee": {
                "name": session.persona.name,
                "employee_id": session.persona.employee_id or "N/A",
                "role": session.persona.role,
                "department": session.persona.department or "Engineering",
                "team": session.persona.team,
                "manager_name": session.persona.manager_name or "N/A",
                "manager_email": session.persona.manager_email or "manager@novabyte.dev",
                "mentor_name": session.persona.mentor_name or "N/A",
                "mentor_email": session.persona.mentor_email or "mentor@novabyte.dev",
                "start_date": session.persona.start_date or "N/A",
                "location": session.persona.location or "N/A",
                "email": session.persona.email,
                "tech_stack": session.persona.tech_stack,
            },
            "summary": {
                "status": "COMPLETED",
                "completion_date": completion_time.date().isoformat(),
                "completion_timestamp_iso": completion_time.isoformat(),
                "total_duration_business_days": business_days,
            },
            "checklist_summary": {
                "total_tasks": total_tasks,
                "completed_count": completed_count,
                "completed_percentage": completed_percentage,
                "skipped_count": 0,
                "pending_count": pending_count,
            },
            "completed_items": [
                {
                    "code": item.checklist_code,
                    "title": item.title,
                    "completed_at": item.completed_at,
                }
                for item in completed_items
            ],
            "pending_items": [
                {
                    "code": item.checklist_code,
                    "title": item.title,
                    "reason": "Not completed",
                }
                for item in pending_items
            ],
            "compliance_status": compliance_status,
            "access_provisioned": access_provisioned,
            "first_task_status": {
                "ticket": f"{ticket_id}: {ticket_title}",
                "status": self._task_status_for_first_ticket(session),
                "pr_link": "N/A",
            },
            "confidence_score": round(confidence * 100, 2),
            "notes": "Generated from PS03 dataset: KB-006, KB-007, KB-009, KB-010.",
            "source_template": {
                "document_id": "KB-009",
                "template": "Template 1: Onboarding Completion Notification",
                "template_loaded": bool(self._completion_template),
            },
            "delivery_status": "sent",
            "report_id": report_id,
            "generated_at": completion_time.isoformat(),
        }

        completed_lines = "\n".join(
            [f"[✓] {item.checklist_code} {item.title}" for item in completed_items[:20]]
        )
        if not completed_lines:
            completed_lines = "None"

        pending_lines = "\n".join(
            [f"[○] {item.checklist_code} {item.title}" for item in pending_items[:20]]
        )
        if not pending_lines:
            pending_lines = "None"

        body = (
            "ONBOARDING COMPLETION REPORT\n"
            "=============================\n\n"
            "Employee Information\n"
            "--------------------\n"
            f"Name:               {payload['employee']['name']}\n"
            f"Employee ID:        {payload['employee']['employee_id']}\n"
            f"Role:               {payload['employee']['role']}\n"
            f"Department:         {payload['employee']['department']}\n"
            f"Team:               {payload['employee']['team']}\n"
            f"Manager:            {payload['employee']['manager_name']}\n"
            f"Mentor/Buddy:       {payload['employee']['mentor_name']}\n"
            f"Start Date:         {payload['employee']['start_date']}\n"
            f"Location:           {payload['employee']['location']}\n\n"
            "Onboarding Summary\n"
            "------------------\n"
            f"Status:             {payload['summary']['status']}\n"
            f"Completion Date:    {payload['summary']['completion_date']}\n"
            f"Completion Time:    {payload['summary']['completion_timestamp_iso']}\n"
            f"Total Duration:     {payload['summary']['total_duration_business_days']} business days\n\n"
            "Checklist Summary\n"
            "-----------------\n"
            f"Total Tasks:        {payload['checklist_summary']['total_tasks']}\n"
            f"Completed:          {payload['checklist_summary']['completed_count']} ({payload['checklist_summary']['completed_percentage']}%)\n"
            f"Skipped:            {payload['checklist_summary']['skipped_count']}\n"
            f"Pending:            {payload['checklist_summary']['pending_count']}\n\n"
            "Completed Items\n"
            "---------------\n"
            f"{completed_lines}\n\n"
            "Pending Items\n"
            "-------------\n"
            f"{pending_lines}\n\n"
            "First Task Status\n"
            "-----------------\n"
            f"Ticket:             {payload['first_task_status']['ticket']}\n"
            f"Status:             {payload['first_task_status']['status']}\n"
            f"PR Link:            {payload['first_task_status']['pr_link']}\n\n"
            "Confidence Score\n"
            "----------------\n"
            f"Onboarding Completeness:   {payload['confidence_score']}%\n\n"
            f"Report ID: {report_id}\n"
            f"Generated At: {completion_time.isoformat()}\n"
        )

        return CompletionEmail(
            to=payload["to"],
            subject=payload["subject"],
            body=body,
            payload=payload,
        )
