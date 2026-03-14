"""Mock MCP (Model Context Protocol) gateway for internal enterprise tools."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: dict


@router.post("/execute_tool")
async def execute_tool(request: ToolCallRequest):
    """
    Mock endpoint for tool execution.
    It simulates downstream integrations used by onboarding workflows.
    """
    if request.tool_name == "provision_github_access":
        return {
            "status": "success",
            "message": f"Added user {request.arguments.get('username')} to GitHub org.",
        }

    if request.tool_name == "assign_jira_ticket":
        return {
            "status": "success",
            "ticket_id": "ONB-001",
            "message": "First-week ticket assigned.",
        }

    if request.tool_name == "invite_to_slack":
        return {
            "status": "success",
            "channel": request.arguments.get("channel", "#engineering-onboarding"),
            "message": f"Invited {request.arguments.get('email')} to onboarding channel.",
        }

    if request.tool_name == "send_slack_welcome":
        return {
            "status": "success",
            "channel": request.arguments.get("channel", "#new-joiners"),
            "message": f"Posted welcome message for {request.arguments.get('name')}.",
        }

    if request.tool_name == "send_hr_completion_email":
        return {
            "status": "success",
            "message": "Structured onboarding completion email sent to HR.",
            "email_subject": request.arguments.get("subject"),
            "employee": request.arguments.get("employee"),
        }

    return {"status": "error", "message": "Unknown tool."}
