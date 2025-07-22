from pydantic_ai import RunContext

from configs.logger import logger
from src.helpers import get_http_client
from src.ai_agent.utils import AgentDeps


# Tool: Get answers from Knowledge Base
async def custom_knowledge_tool(ctx: RunContext[AgentDeps], query: str) -> str:
    """
    Fetch answers from custom knowledge base.

    Args:
        query: The query string to search for in the custom knowledge base.

    Returns:
        A list of document chunks containing relevant information from the custom knowledge base.
    """
    try:
        client = get_http_client()
        base_url = ctx.deps.quadsearch_base_url
        api_key = ctx.deps.quadsearch_api_key
        data = {
            "query": query,
            "limit": 5,
            "collection_name": ctx.deps.collection_name,
        }

        response = await client.post(
            f"{base_url}/api/v1/qdrant/search",
            json=data,
            headers={"Authorization": api_key},
        )

        data = response.json()
        logger.info(f"Fetched answers for query: '{query}': {data}")
        if data:
            # Format the list of document chunks
            formatted_chunks = [
                f"Content: {item['payload']['content']}\n"
                for item in data.get('data', [])
            ]
            # logger.info(f"Formatted chunks: {formatted_chunks}")
            return "\n\n".join(formatted_chunks)
        else:
            return "Error fetching answers. Please try again later."

    except Exception as e:
        logger.error(f"Error reaching quadsearch server: {str(e)}")
        return "Error fetching answers. Please try again later."
