from onboarding_service import OnboardingOrchestrator


def test_profile_collection_generates_checklist():
    orchestrator = OnboardingOrchestrator()
    session = orchestrator.create_session()

    first = orchestrator.handle_chat(session.session_id, "My name is Riley")
    assert "role" in first["missing_profile_fields"]

    second = orchestrator.handle_chat(
        session.session_id,
        "I am a backend junior engineer using Python",
    )

    assert second["missing_profile_fields"] == []
    assert len(second["checklist"]) >= 6
    assert second["profile"]["role"] == "backend"
    assert "python" in second["profile"]["tech_stack"]


def test_retrieval_response_contains_sources():
    orchestrator = OnboardingOrchestrator()
    session = orchestrator.create_session()

    orchestrator.update_profile(
        session_id=session.session_id,
        name="Casey",
        role="frontend",
        experience_level="intern",
        tech_stack=["node"],
    )

    response = orchestrator.handle_chat(session.session_id, "How do I set up the frontend service?")

    assert response["sources"]
    assert response["sources"][0]["source_id"].startswith("ENG-")


def test_completion_requires_all_tasks_done():
    orchestrator = OnboardingOrchestrator()
    session = orchestrator.create_session()
    orchestrator.update_profile(
        session_id=session.session_id,
        name="Jordan",
        role="devops",
        experience_level="senior",
        tech_stack=["go"],
    )

    try:
        orchestrator.complete_onboarding(session.session_id)
        assert False, "Expected ValueError when pending tasks exist"
    except ValueError as exc:
        assert "pending" in str(exc).lower()

    refreshed = orchestrator.get_session(session.session_id)
    assert refreshed is not None

    for item in refreshed.checklist:
        orchestrator.mark_item(session.session_id, item.item_id, True)

    completion = orchestrator.complete_onboarding(session.session_id)
    assert completion.payload["summary"]["status"] == "Completed"
    assert completion.payload["delivery_status"] == "sent"
