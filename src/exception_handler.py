from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.auth.exceptions import APIKeyException

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Collect error messages for each field
    errors = [
        f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()
    ]
    # Combine errors into a single message
    error_message = "; ".join(errors)

    # Custom error response
    return JSONResponse(
        status_code=422,
        content={
            "status": 422,
            "message": error_message,
            "data": {}
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": 500,
            "message": "Something went wrong!",
            "data": {}
        },
    )


@app.exception_handler(APIKeyException)
async def api_key_exception_handler(request: Request, exc: APIKeyException):
    return JSONResponse(
        status_code=401,
        content={
            "status": 401,
            "message": exc.message,
            "data": {}
        }
    )
