# PS-03: Autonomous Developer Onboarding Agent

This monorepo now implements a working **agentic onboarding platform** for the PS-03 hackathon problem:

- Chat-based onboarding flow
- Persona-aware onboarding path generation (role + experience + tech stack)
- Structured knowledge retrieval with source citations (RAG-style grounding)
- Checklist tracking with real-time progress
- Structured HR completion email generation (mock-sent)

## Services

1. `frontend/` (Next.js): chat UI + checklist dashboard + HR completion preview
2. `agent/` (FastAPI): onboarding orchestrator, retrieval, checklist/state engine, HR report generation
3. `backend/` (FastAPI): user/checklist CRUD scaffold (kept for extensibility)
4. `db` + `redis` via Docker Compose

## Run Locally

```bash
docker-compose up --build
```

Endpoints:

- Frontend: `http://localhost:3000`
- Agent API: `http://localhost:8001/docs`
- Backend API: `http://localhost:8000/docs`

## Agent API (Core)

### Start or continue onboarding through chat

`POST /chat`

```json
{
  "session_id": "optional-session-id",
  "message": "My name is Alex. I am a backend junior using Python."
}
```

The response includes:

- `message` (agent reply)
- `sources` (knowledge citations)
- `profile` (captured onboarding persona)
- `checklist`
- `progress_percent`
- `status` (`in_progress` or `completed`)
- `missing_profile_fields`

### Update checklist item

`PATCH /onboarding/session/{session_id}/checklist/{item_id}`

### Finalize onboarding and notify HR

`POST /onboarding/session/{session_id}/complete`

Returns a structured HR payload including employee details, completed/pending items, completion timestamp, and confidence score.

## Knowledge Retrieval Design

The agent uses a structured local knowledge base (`agent/knowledge_base.py`) and lexical scoring with role/stack weighting. Responses are constrained to retrieved sources and include source IDs in replies to reduce hallucination risk.

## Personalization Logic

Checklist composition is generated from:

- `role`: backend | frontend | devops
- `experience_level`: intern | junior | senior
- `tech_stack`: python | node | java | go | rust | typescript

Each path combines base tasks + role-specific + level-specific + stack-specific tasks.

## Tests

- Backend smoke tests: `backend/tests/test_api.py`
- Agent orchestration tests: `agent/tests/test_onboarding_service.py`

Run examples:

```bash
cd backend && pytest
cd ../agent && PYTHONPATH=. pytest
```
