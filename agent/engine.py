from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List

from mcp_server import router as mcp_router
from onboarding_service import (
    ALLOWED_EXPERIENCE_LEVELS,
    ALLOWED_ROLES,
    KNOWN_STACKS,
    OnboardingOrchestrator,
    Persona,
)

app = FastAPI(title="PS-03 Agent API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mcp_router, prefix="/mcp", tags=["MCP Tools"])

orchestrator = OnboardingOrchestrator()


class StartSessionRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    team: Optional[str] = None
    role: Optional[str] = None
    experience_level: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    team: Optional[str] = None
    role: Optional[str] = None
    experience_level: Optional[str] = None
    tech_stack: Optional[List[str]] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChecklistUpdateRequest(BaseModel):
    is_completed: bool


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "service": "ps03-agent"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/onboarding/session")
async def start_session(request: StartSessionRequest) -> dict:
    role = request.role.lower() if request.role and request.role.lower() in ALLOWED_ROLES else None
    experience_level = (
        request.experience_level.lower()
        if request.experience_level and request.experience_level.lower() in ALLOWED_EXPERIENCE_LEVELS
        else None
    )
    tech_stack = [stack.lower() for stack in request.tech_stack if stack.lower() in KNOWN_STACKS]

    persona_seed = Persona(
        name=request.name,
        email=request.email,
        team=request.team,
        role=role,
        experience_level=experience_level,
        tech_stack=tech_stack,
    )
    session = orchestrator.create_session(persona_seed=persona_seed)
    return {
        "session_id": session.session_id,
        "status": session.status,
        "profile": {
            "name": session.persona.name,
            "email": session.persona.email,
            "team": session.persona.team,
            "role": session.persona.role,
            "experience_level": session.persona.experience_level,
            "tech_stack": session.persona.tech_stack,
        },
        "checklist": [
            {
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
            for item in session.checklist
        ],
        "progress_percent": session.progress_percent,
        "missing_profile_fields": session.persona.missing_fields(),
        "assigned_ticket": orchestrator.serialize_ticket(session.assigned_ticket),
        "inference_notes": session.inference_notes,
    }


@app.get("/onboarding/session/{session_id}")
async def get_session(session_id: str) -> dict:
    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.session_id,
        "status": session.status,
        "profile": {
            "name": session.persona.name,
            "email": session.persona.email,
            "team": session.persona.team,
            "role": session.persona.role,
            "experience_level": session.persona.experience_level,
            "tech_stack": session.persona.tech_stack,
        },
        "checklist": [
            {
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
            for item in session.checklist
        ],
        "progress_percent": session.progress_percent,
        "missing_profile_fields": session.persona.missing_fields(),
        "completion_email": session.completion_email.payload if session.completion_email else None,
        "assigned_ticket": orchestrator.serialize_ticket(session.assigned_ticket),
        "inference_notes": session.inference_notes,
    }


@app.patch("/onboarding/session/{session_id}/profile")
async def update_profile(session_id: str, request: UpdateProfileRequest) -> dict:
    try:
        session = orchestrator.update_profile(
            session_id=session_id,
            name=request.name,
            email=request.email,
            team=request.team,
            role=request.role,
            experience_level=request.experience_level,
            tech_stack=request.tech_stack,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "session_id": session.session_id,
        "profile": {
            "name": session.persona.name,
            "email": session.persona.email,
            "team": session.persona.team,
            "role": session.persona.role,
            "experience_level": session.persona.experience_level,
            "tech_stack": session.persona.tech_stack,
        },
        "status": session.status,
        "progress_percent": session.progress_percent,
        "missing_profile_fields": session.persona.missing_fields(),
        "checklist": [
            {
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
            for item in session.checklist
        ],
        "assigned_ticket": orchestrator.serialize_ticket(session.assigned_ticket),
        "inference_notes": session.inference_notes,
    }


@app.patch("/onboarding/session/{session_id}/checklist/{item_id}")
async def update_checklist_item(session_id: str, item_id: int, request: ChecklistUpdateRequest) -> dict:
    try:
        session = orchestrator.mark_item(
            session_id=session_id,
            item_id=item_id,
            is_completed=request.is_completed,
        )
    except ValueError as exc:
        message = str(exc)
        code = 404 if "not found" in message.lower() else 400
        raise HTTPException(status_code=code, detail=message) from exc

    return {
        "session_id": session.session_id,
        "status": session.status,
        "progress_percent": session.progress_percent,
        "checklist": [
            {
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
            for item in session.checklist
        ],
        "assigned_ticket": orchestrator.serialize_ticket(session.assigned_ticket),
        "inference_notes": session.inference_notes,
    }


@app.post("/onboarding/session/{session_id}/complete")
async def complete_onboarding(session_id: str) -> dict:
    try:
        completion_email = orchestrator.complete_onboarding(session_id)
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "session" in message.lower() else 400
        raise HTTPException(status_code=status_code, detail=message) from exc

    return {
        "session_id": session_id,
        "status": "completed",
        "completion_email": completion_email.payload,
        "email_preview": completion_email.body,
    }


@app.post("/chat")
async def chat(request: ChatRequest) -> dict:
    session_id = request.session_id
    if not session_id:
        session = orchestrator.create_session()
        session_id = session.session_id

    try:
        response = orchestrator.handle_chat(session_id=session_id, message=request.message)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return response
