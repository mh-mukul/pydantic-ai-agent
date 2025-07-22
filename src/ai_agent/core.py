import os
from typing import List
from datetime import datetime
from dotenv import load_dotenv

from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelRequest,
    SystemPromptPart
)
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from configs.logger import logger

from src.auth.models import User
from src.ai_agent.models import ChatHistory
from src.ai_agent.tools import custom_knowledge_tool
from src.ai_agent.utils import AgentDeps, to_pydantic_ai_message

# Load environment variables from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_GLA_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash-001")

gemini_model = GeminiModel(
    GEMINI_MODEL_NAME, provider=GoogleGLAProvider(api_key=GEMINI_API_KEY)
)

# Initialize the agent with the Gemini model and tools
ai_agent = Agent(
    model=gemini_model,
    tools=[custom_knowledge_tool]
)


async def execute_agent(
    user: User,
    user_message: str,
    messages: List[ChatHistory],
    agent_deps: AgentDeps
) -> str:
    """
    Execute the agent with the provided user info and message history.
    Args:
        user (User): The user object containing user details.
        user_message (str): The message from the user.
        messages (List[ChatHistory]): The conversation history.
        agent_deps (AgentDeps): Dependencies required by the agent.
    Returns:
        str: The output from the agent.
    """
    # Convert ChatHistory messages to Pydantic AI ModelMessage format
    history = to_pydantic_ai_message(messages)
    # Prepend system prompt message
    prompt = f"""You are a helpful AI Assistant.

    ## Important Instructions:
    - ALWAYS address the user by name. User's name is {user.name}.
    - Use the custom_knowledge_tool to answer users queries when needed.
    - Today's date is: {datetime.now().strftime('%Y-%m-%d')} & today is {datetime.now().strftime('%A')}.
    - NEVER talk about your tools & it's usage or your data retrieval process.
    """
    # Prepend system prompt message
    system_msg = ModelRequest(parts=[SystemPromptPart(content=prompt)])
    messages_with_prompt = [system_msg] + history
    # Run the agent with message history
    result = await ai_agent.run(user_prompt=user_message, message_history=messages_with_prompt, deps=agent_deps)
    output = result.output
    logger.info(f"Agent run details: {result.all_messages()}")

    return output
