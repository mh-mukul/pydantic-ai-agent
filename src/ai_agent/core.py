import os
from typing import List
from datetime import datetime
from dotenv import load_dotenv

from ddgs import DDGS
from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelRequest,
    SystemPromptPart
)
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

from configs.logger import logger

from src.auth.models import User
from src.ai_agent.models import ChatMessage
from src.ai_agent.tools import custom_knowledge_tool
from src.ai_agent.utils import AgentDeps, to_pydantic_ai_message

# Load environment variables from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_GLA_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

gemini_model = GeminiModel(
    GEMINI_MODEL_NAME, provider=GoogleGLAProvider(api_key=GEMINI_API_KEY)
)

# Initialize the agent with the Gemini model and tools
ai_agent = Agent(
    model=gemini_model,
    tools=[duckduckgo_search_tool(duckduckgo_client=DDGS(), max_results=5)],
)


async def execute_agent(
    user_name: str,
    user_message: str,
    messages: List[ChatMessage],
    agent_deps: AgentDeps,
    stream: bool = False
):
    """
    Execute the agent with the provided user info and message history.
    Args:
        user_name (str): The name of the user.
        user_message (str): The message from the user.
        messages (List[ChatMessage]): The conversation history.
        agent_deps (AgentDeps): Dependencies required by the agent.
        stream (bool): Whether to stream the output. Defaults to False.
    Returns:
        If stream=True: async generator yielding ONLY new string chunks
        If stream=False: str containing the complete output
    """
    # Convert ChatMessage messages to Pydantic AI ModelMessage format
    history = to_pydantic_ai_message(messages)

    # Prepend system prompt message
    prompt = f"""You are a helpful AI Assistant.

    ## Important Instructions:
    - ALWAYS address the user by name. User's name is {user_name}.
    - Use the duckduckgo_search_tool to search the web and get relevant information.
    - Today's date is: {datetime.now().strftime('%Y-%m-%d')} & today is {datetime.now().strftime('%A')}.
    """
    system_msg = ModelRequest(parts=[SystemPromptPart(content=prompt)])
    messages_with_prompt = [system_msg] + history

    if stream:
        async def generator():
            async with ai_agent.run_stream(
                user_prompt=user_message,
                message_history=messages_with_prompt,
                deps=agent_deps
            ) as streamed_result:
                prev_len = 0
                async for partial_text in streamed_result.stream_text():
                    # Only send the new portion to avoid duplication
                    new_chunk = partial_text[prev_len:]
                    prev_len = len(partial_text)
                    if new_chunk:
                        yield new_chunk
        return generator()

    else:
        result = await ai_agent.run(
            user_prompt=user_message,
            message_history=messages_with_prompt,
            deps=agent_deps
        )
        logger.info(f"Agent run details: {result.all_messages()}")
        return result.output


async def execute_metadata_agent(
    user_message: str
) -> str:
    """
    Execute the metadata agent with the provided user message.
    Args:
        user_message (str): The message from the user.
    Returns:
        str: The output from the metadata agent.
    """
    prompt = f"""You are a helpful AI Assistant. Your purpose is to extract a short title from the user's query.\n
    If the query is not relevant for a title, respond with "New chat". You do not answer any query only response with the plain title.\n
    """
    metadata_agent = Agent(
        model=gemini_model,
        system_prompt=prompt,
    )
    # Run the metadata agent with the user message
    result = await metadata_agent.run(user_prompt=user_message)
    output = result.output.replace("\n", " ").strip()
    logger.info(f"Metadata agent run details: {result.all_messages()}")

    return output
