import os
import json
from typing import List
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from datetime import datetime, timezone

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
from src.ai_agent.schemas import ChatGetResponse
from src.ai_agent.tools import custom_knowledge_tool
from src.ai_agent.utils import AgentDeps, to_pydantic_ai_message, save_conversation_history

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
    user: User,
    user_message: str,
    messages: List[ChatMessage],
    agent_deps: AgentDeps,
    stream: bool = False,
    sse_mode: bool = False,
    session_id: str = None,
    chat: ChatMessage = None,
    db: Session = None,
    start_time: datetime = None
):
    """
    Execute the AI agent with the provided user message and conversation history.
    Args:
        user (User): The user object.
        user_message (str): The message from the user.
        messages (List[ChatMessage]): Conversation history.
        agent_deps (AgentDeps): Dependencies for the agent.
        stream (bool): Whether to stream the response.
        sse_mode (bool): Whether to use Server-Sent Events mode.
        session_id (str): The session ID for the chat.
        chat (ChatMessage): Optional existing chat message to update.
        db (Session): Database session for saving chat history.
        start_time (datetime): Start time for measuring duration.
    Returns:
        str or generator: The output from the agent or a generator for streaming responses.
    """
    # Convert ChatMessage objects to Pydantic AI message format
    history = to_pydantic_ai_message(messages)

    prompt = f"""You are a helpful AI Assistant.

    ## Important Instructions:
    - ALWAYS address the user by name. User's name is {user.name}.
    - Use the duckduckgo_search_tool to search the web if you need up to date information on something.
    - Include the source of search results in markdown format like this: `Source: [Source 1](https://www.source1.com/news/abc), [Source 2](https://www.source2.com/news/abc), etc`, if you use the duckduckgo_search_tool.
    - Today's date is: {datetime.now().strftime('%Y-%m-%d')} & today is {datetime.now().strftime('%A')}.
    """
    system_msg = ModelRequest(parts=[SystemPromptPart(content=prompt)])
    messages_with_prompt = [system_msg] + history

    if stream:
        async def generator():
            full_output = ""
            prev_len = 0
            async with ai_agent.run_stream(
                user_prompt=user_message,
                message_history=messages_with_prompt,
                deps=agent_deps
            ) as streamed_result:
                async for partial_text in streamed_result.stream_text():
                    # Delta logic
                    new_chunk = partial_text[prev_len:]
                    prev_len = len(partial_text)
                    if not new_chunk:
                        continue

                    full_output += new_chunk
                    if sse_mode:
                        yield f"event: chunk\ndata: {json.dumps({'text': new_chunk})}\n\n"
                    else:
                        yield new_chunk

            # Only save + send done event in SSE mode
            if sse_mode and db and session_id:
                if not chat:
                    chat_message = await save_conversation_history(
                        session_id=session_id,
                        human_message=user_message,
                        ai_message=full_output,
                        date_time=datetime.now(tz=timezone.utc),
                        duration=(datetime.now(tz=timezone.utc) -
                                  start_time).total_seconds() if start_time else None,
                        db=db
                    )
                else:
                    chat.human_message = user_message
                    chat.ai_message = full_output
                    chat.date_time = datetime.now(tz=timezone.utc)
                    chat.duration = (datetime.now(
                        tz=timezone.utc) - start_time).total_seconds() if start_time else None
                    chat.positive_feedback = False
                    chat.negative_feedback = False
                    db.add(chat)
                    db.commit()
                    db.refresh(chat)
                    chat_message = chat
                done_payload = {
                    "status": 200,
                    "message": "success",
                    "data": ChatGetResponse.model_validate(chat_message).model_dump(mode="json")
                }
                yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

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
