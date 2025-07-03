import json

from pydantic_ai import RunContext

from configs.logger import logger
from src.helpers import get_http_client
from src.ai_agent.utils import AgentDeps


# Tool: Get FAQs from HRIS Knowledge Base
async def get_hris_faqs(ctx: RunContext[AgentDeps], query: str) -> str:
    """
    Fetch faq answers from HRIS knowledge base.

    Args:
        query: The query string to search for in the HRIS knowledge base.

    Returns:
        A list of document chunks containing relevant information from the HRIS knowledge base.
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
        logger.info(f"Fetched HRIS FAQs for query: '{query}': {data}")
        if data:
            # Format the list of document chunks
            formatted_chunks = [
                f"Content: {item['payload']['content']}\n"
                for item in data.get('data', [])
            ]
            # logger.info(f"Formatted HRIS FAQs: {formatted_chunks}")
            return "\n\n".join(formatted_chunks)
        else:
            return "Error fetching HRIS FAQs. Please try again later."

    except Exception as e:
        logger.error(f"Error reaching quadsearch server: {str(e)}")
        return "Error fetching HRIS FAQs. Please try again later."


# Tool: Get Employee Info from HRIS
async def get_employee_info(ctx: RunContext[AgentDeps], employee_id: int) -> str:
    """
    Fetch employee information from the HRIS system.

    Args:
        employee_id: The employee ID of the current user.

    Returns:
        A JSON response containing employee information.
    """
    try:
        client = get_http_client()
        base_url = ctx.deps.hris_base_url
        token = ctx.deps.hris_token
        params = {'query': employee_id}

        response = await client.get(
            f"{base_url}/api/v1/get-employee-details",
            params=params,
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.json()
        logger.info(f"Fetched employee info for ID {employee_id}: {data}")
        if data:
            return json.dumps(data, indent=2)
        else:
            return "Employee information not found."

    except Exception as e:
        logger.error(f"Error reaching HRIS server: {str(e)}")
        return "Error fetching employee information. Please try again later."


# Tool: Get Employee Leave Balance from HRIS
async def get_employee_leave(ctx: RunContext[AgentDeps], employee_id: int) -> str:
    """
    Fetch employee available leave balance from the HRIS system.

    Args:
        employee_id: The employee ID of the current user.

    Returns:
        A JSON response containing information about employee available leave balance.
    """
    try:
        client = get_http_client()
        base_url = ctx.deps.hris_base_url
        token = ctx.deps.hris_token
        params = {'emp_id': employee_id}

        response = await client.get(
            f"{base_url}/api/v1/employee-leave-amount",
            params=params,
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.json()
        logger.info(
            f"Fetched employee leave balance for ID {employee_id}: {data}")
        if data:
            return json.dumps(data, indent=2)
        else:
            return "Employee leave information not found."

    except Exception as e:
        logger.error(f"Error reaching HRIS server: {str(e)}")
        return "Error fetching employee information. Please try again later."
