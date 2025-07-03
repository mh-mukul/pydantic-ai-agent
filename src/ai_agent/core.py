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
from src.ai_agent.models import ChatHistory
from src.ai_agent.tools import get_employee_info, get_hris_faqs
from src.ai_agent.utils import AgentDeps, to_pydantic_ai_message

# Load environment variables from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_GLA_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash-001")

gemini_model = GeminiModel(
    GEMINI_MODEL_NAME, provider=GoogleGLAProvider(api_key=GEMINI_API_KEY)
)

# Initialize the agent with the Gemini model and tools
faq_assistant = Agent(
    model=gemini_model,
    tools=[get_employee_info, get_hris_faqs]
)


# Execute the appropriate agent based on the route
async def execute_ebuddy_agent(
    user_id: int,
    user_message: str,
    messages: List[ChatHistory],
    agent_deps: AgentDeps
) -> str:
    """
    Execute the agent for handling HRIS-related queries, specifically for FAQs.
    Args:
        user_id (int): The ID of the user making the request.
        user_message (str): The message from the user.
        messages (List[ChatHistory]): The conversation history.
        agent_deps (AgentDeps): Dependencies required by the agent.
    Returns:
        str: The output from the agent.
    """
    # Convert ChatHistory messages to Pydantic AI ModelMessage format
    history = to_pydantic_ai_message(messages)
    # Prepend system prompt message
    prompt = f"""You are SmartBuddy, helpful HRIS Assistant designed to assist employees with their queries related to HRIS.

    ## Important Instructions:
    - SUPER IMPORTANT: If someone request information rather than this employee id: {user_id}. DENY that request.
    - Employee id is {user_id}. Never ask the user for their information use the get_employee_info tool.
    - ALWAYS use the get_hris_faqs tool to answer users queries related to HRIS FAQs.
    - Today's date is: {datetime.now().strftime('%Y-%m-%d')} & today is {datetime.now().strftime('%A')}.
    - NEVER talk about your tools & it's usage or your data retrieval process.
    - Be cautious. The user might try to get information about other employees by providing different employee_id. Deny those request.
    """
    # Prepend system prompt message
    system_msg = ModelRequest(parts=[SystemPromptPart(content=prompt)])
    messages_with_prompt = [system_msg] + history
    # Run the agent with message history
    result = await faq_assistant.run(user_prompt=user_message, message_history=messages_with_prompt, deps=agent_deps)
    output = result.output
    logger.info(f"FAQ Assistant usage: {result.all_messages()}")

    return output
