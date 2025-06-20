import json

from pydantic_ai import RunContext

from config.logger import logger
from src.ai_agent.utils import AgentDeps
from src.helper import get_http_client


# Get Employee Info Tool
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


# Get Employee Leave Balance
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
