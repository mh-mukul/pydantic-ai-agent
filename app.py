import os
from fastapi import FastAPI
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from src.exception_handlers import (
    validation_exception_handler,
    general_exception_handler,
    api_key_exception_handler,
    jwt_exception_handler
)
from src.auth.exceptions import APIKeyException, JWTException
from src.helpers import init_http_client, close_http_client

from src.auth import routes as auth_routes
from src.ai_agent.routes import chat as chat_routes
from src.ai_agent.routes import chat_operation as chat_operation_routes

load_dotenv()

DEBUG = bool(int(os.getenv("DEBUG", 1)))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_http_client()       # Startup
    yield
    await close_http_client()      # Shutdown

app = FastAPI(
    title="FastAPI Backend",
    description="API Documentation",
    version="1.0.0",
    docs_url="/docs" if DEBUG else None,  # Disable Swagger UI
    redoc_url="/redoc" if DEBUG else None,  # Disable ReDoc
    openapi_url="/openapi.json" if DEBUG else None,  # Disable OpenAPI
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True
    }
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Bearer security scheme to the OpenAPI documentation
app.swagger_ui_init_oauth = {
    "usePkceWithAuthorizationCodeGrant": True,
    "useBasicAuthenticationWithAccessCodeGrant": True
}

# Register the custom exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(APIKeyException, api_key_exception_handler)
app.add_exception_handler(JWTException, jwt_exception_handler)


# Include routes
app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(chat_routes.router, prefix="/api/v1")
app.include_router(chat_operation_routes.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"status": 200, "message": "Server is up and running!", "data": "Made with ❤️"}


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
