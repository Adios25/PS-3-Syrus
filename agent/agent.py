from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic_settings import BaseSettings

class AgentSettings(BaseSettings):
    OPENAI_API_KEY: str = ""
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_TRACING_V2: str = "true"

    class Config:
        env_file = ".env"

settings = AgentSettings()

# Example Initialization - Ensure API Key is passed via ENV
llm = ChatOpenAI(model="gpt-4", temperature=0)

system_prompt = SystemMessage(
    content="""You are an expert Autonomous Developer Onboarding Agent (PS-03).
Your job is to guide new developers through their onboarding checklist, answer technical questions about the enterprise architecture, and assist with initial access provisioning."""
)

async def generate_response(user_input: str) -> str:
    messages = [
        system_prompt,
        HumanMessage(content=user_input)
    ]
    response = await llm.ainvoke(messages)
    return response.content
