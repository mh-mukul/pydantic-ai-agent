from httpx import AsyncClient


class ResponseHelper:
    def success_response(self, status_code, message, data=None):
        return ({
            "status": status_code,
            "message": message,
            "data": data
        })

    def error_response(self, status_code, message, data=None):
        return ({
            "status": status_code,
            "message": message,
            "data": data
        })


_http_client: AsyncClient | None = None


async def init_http_client():
    global _http_client
    if _http_client is None:
        _http_client = AsyncClient()


async def close_http_client():
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None


def get_http_client() -> AsyncClient:
    if _http_client is None:
        raise RuntimeError(
            "HTTP client not initialized. Call init_http_client() on startup.")
    return _http_client
