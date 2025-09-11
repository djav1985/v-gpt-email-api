"""Application entry point configuring routes and startup behavior."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiofiles
from fastapi import FastAPI, HTTPException, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from . import dependencies
from .config import Config
from .routes.imap import imap_router
from .routes.read_email import read_router
from .routes.send_email import send_router

tags_metadata = [
    {"name": "Send", "description": "Endpoints for sending emails"},
    {"name": "Read", "description": "Endpoints for reading emails"},
    {"name": "IMAP", "description": "Low-level IMAP operations"},
]


@asynccontextmanager
async def lifespan(app) -> AsyncGenerator[None, None]:
    """Load configuration and signature text at startup."""
    try:
        dependencies.settings = Config(
            account_email=os.getenv("ACCOUNT_EMAIL", ""),
            account_password=os.getenv("ACCOUNT_PASSWORD", ""),
            account_smtp_server=os.getenv("ACCOUNT_SMTP_SERVER", ""),
            account_smtp_port=int(os.getenv("ACCOUNT_SMTP_PORT", "587")),
            account_imap_server=os.getenv("ACCOUNT_IMAP_SERVER", ""),
            account_imap_port=int(os.getenv("ACCOUNT_IMAP_PORT", "993")),
            api_key=os.getenv("API_KEY", ""),
            from_name=os.getenv("FROM_NAME", ""),
            attachment_concurrency=int(os.getenv("ATTACHMENT_CONCURRENCY", "3")),
            start_tls=os.getenv("START_TLS", "true").lower() == "true",
            account_reply_to=os.getenv("ACCOUNT_REPLY_TO", None),
        )
    except ValidationError as exc:
        missing = [
            ".".join(str(loc) for loc in err["loc"]).upper()
            for err in exc.errors()
            if err.get("type") == "missing"
        ]
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        ) from exc

    try:
        async with aiofiles.open("app/config/signature.txt", "r") as file:
            dependencies.signature_text = await file.read()
    except FileNotFoundError:
        dependencies.signature_text = ""
    yield


# FastAPI application instance
app = FastAPI(
    title="Email Management API",
    version="0.1.0",
    description="A FastAPI to send emails",
    openapi_version="3.1.0",
    openapi_tags=tags_metadata,
    root_path=os.getenv("ROOT_PATH", "/"),
    root_path_in_servers=False,
    servers=[
        {
            "url": f"{os.getenv('BASE_URL', '')}{os.getenv('ROOT_PATH', '/')}",
            "description": "Base API server",
        }
    ],
    lifespan=lifespan,
)

# Include routers
app.include_router(send_router)
app.include_router(read_router)
app.include_router(imap_router)


def custom_openapi() -> dict:
    """Generate and cache a custom OpenAPI schema for the app."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=tags_metadata,
        servers=app.servers,
    )
    # Add API key authentication scheme
    openapi_schema.setdefault("components", {}).setdefault(
        "securitySchemes", {}
    )["ApiKeyAuth"] = {
        "type": "apiKey",
        "name": "X-API-Key",
        "in": "header",
        "description": "Provide the API key via the X-API-Key header"
    }
    openapi_schema["openapi"] = "3.1.0"
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return JSON errors for HTTPException instances."""
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
