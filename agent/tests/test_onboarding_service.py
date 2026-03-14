from onboarding_service import OnboardingOrchestrator


def test_dataset_driven_personalization_and_checklist_generation():
    orchestrator = OnboardingOrchestrator()
    session = orchestrator.create_session()

    response = orchestrator.handle_chat(
        session.session_id,
        "Hi, I'm Riya. I've joined as a Backend Intern working on Node.js in Squad Beta.",
    )

    assert response["missing_profile_fields"] == []
    checklist_codes = {item["checklist_code"] for item in response["checklist"]}
    assert "C-01" in checklist_codes
    assert "BI-01" in checklist_codes
    assert response["profile"]["role"] == "backend"
    assert response["profile"]["experience_level"] == "intern"
    assert "node" in response["profile"]["tech_stack"]
    assert response["assigned_ticket"]["ticket_id"] == "FLOW-INTERN-001"


def test_rag_response_is_grounded_to_kb_sources():
    orchestrator = OnboardingOrchestrator()
    session = orchestrator.create_session()

    orchestrator.update_profile(
        session_id=session.session_id,
        name="Sam",
        team="Backend Squad Alpha",
        role="backend",
        experience_level="junior",
        tech_stack=["python"],
    )

    response = orchestrator.handle_chat(session.session_id, "Do I need VPN to access staging?")

    assert response["sources"]
    source_ids = {source["source_id"] for source in response["sources"]}
    assert any(source_id.startswith("KB-") for source_id in source_ids)


def test_completion_email_contains_structured_hr_payload():
    orchestrator = OnboardingOrchestrator()
    session = orchestrator.create_session()

    orchestrator.update_profile(
        session_id=session.session_id,
        name="Meera",
        email="meera.joshi@novabyte.dev",
        team="Platform Team",
        role="devops",
        experience_level="senior",
        tech_stack=["aws", "terraform"],
    )

    refreshed = orchestrator.get_session(session.session_id)
    assert refreshed is not None

    # Completion should fail while pending tasks exist.
    try:
        orchestrator.complete_onboarding(session.session_id)
        assert False, "Expected ValueError when checklist still has pending tasks"
    except ValueError as exc:
        assert "pending" in str(exc).lower()

    for item in refreshed.checklist:
        orchestrator.mark_item(session.session_id, item.item_id, True)

    completion = orchestrator.complete_onboarding(session.session_id)

    assert completion.payload["summary"]["status"] == "COMPLETED"
    assert completion.payload["source_template"]["document_id"] == "KB-009"
    assert completion.payload["delivery_status"] == "sent"
    assert completion.payload["checklist_summary"]["pending_count"] == 0


def test_backend_intern_example_workflow_and_bonus_actions():
    orchestrator = OnboardingOrchestrator()
    session = orchestrator.create_session()

    first = orchestrator.handle_chat(
        session.session_id,
        "Hi, I'm Riya. I've joined as a Backend Intern working on Node.js in Squad Beta.",
    )
    assert "Backend Intern (Node.js)" in first["message"]
    assert first["assigned_ticket"]["ticket_id"] == "FLOW-INTERN-001"

    flow = orchestrator.handle_chat(session.session_id, "Show me the example workflow")
    assert "BI-01" in flow["message"]
    assert "BI-18" in flow["message"]

    mcp = orchestrator.handle_chat(session.session_id, "Please provision all access and send slack welcome")
    assert "MCP actions executed" in mcp["message"]
    tool_names = {entry["tool_name"] for entry in mcp["mcp_actions"]}
    assert "provision_github_access" in tool_names
    assert "invite_to_slack" in tool_names
    assert "assign_jira_ticket" in tool_names
    assert "send_slack_welcome" in tool_names

    env = orchestrator.handle_chat(session.session_id, "verify environment")
    assert "Environment is not fully verified yet" in env["message"]


def test_frontend_senior_flow_and_generated_faq_capture():
    orchestrator = OnboardingOrchestrator()
    session = orchestrator.create_session()

    first = orchestrator.handle_chat(
        session.session_id,
        "I am Neha, senior frontend engineer working on React in Design Systems team.",
    )
    assert "Frontend Senior (React)" in first["message"]

    answer = orchestrator.handle_chat(session.session_id, "How many PR approvals do I need?")
    assert "Based on official onboarding docs" in answer["message"]

    faq = orchestrator.handle_chat(session.session_id, "show generated faq")
    assert "Generated onboarding FAQs captured" in faq["message"]
    assert len(faq["generated_faqs"]) >= 1
