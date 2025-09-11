import os
from typing import AsyncGenerator, Any
import aiofiles
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from . import dependencies
from .routes.send_email import send_router
from .routes.read_email import read_router
from .routes.imap import imap_router


tags_metadata = [
    {"name": "Send", "description": "Endpoints for sending emails"},
    {"name": "Read", "description": "Endpoints for reading emails"},
    {"name": "IMAP", "description": "Low-level IMAP operations"},
]


@asynccontextmanager
async def lifespan(app) -> AsyncGenerator[None, None]:
    required = [
        "ACCOUNT_EMAIL",
        "ACCOUNT_PASSWORD",
        "ACCOUNT_SMTP_SERVER",
        "ACCOUNT_SMTP_PORT",
        "ACCOUNT_IMAP_SERVER",
        "ACCOUNT_IMAP_PORT",
    ]
    env = {var: os.getenv(var) for var in required}
    missing = [var for var, val in env.items() if val is None]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    # All env values are str, not None, so cast for type checkers
    from typing import cast
    smtp_port = int(cast(str, env["ACCOUNT_SMTP_PORT"]))
    imap_port = int(cast(str, env["ACCOUNT_IMAP_PORT"]))

    dependencies.settings = dependencies.Config(
        account_email=cast(str, env["ACCOUNT_EMAIL"]),
        account_password=cast(str, env["ACCOUNT_PASSWORD"]),
        account_smtp_server=cast(str, env["ACCOUNT_SMTP_SERVER"]),
        account_smtp_port=smtp_port,
        account_imap_server=cast(str, env["ACCOUNT_IMAP_SERVER"]),
        account_imap_port=imap_port,
    )
    try:
        async with aiofiles.open("config/signature.txt", "r") as file:
            dependencies.signature_text = await file.read()
    except FileNotFoundError:
        dependencies.signature_text = ""
    yield


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


# Include routers for feature modules
app.include_router(send_router)
app.include_router(read_router)
app.include_router(imap_router)


def custom_openapi() -> dict:
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
    security_scheme = (
        openapi_schema.get("components", {})
        .get("securitySchemes", {})
        .get("HTTPBearer", {})
    )
    if security_scheme:
        security_scheme["description"] = "Provide the API key as a Bearer token"
        security_scheme["bearerFormat"] = "API Key"
    openapi_schema["openapi"] = "3.1.0"
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.exception_handler(HTTPException)
def http_exception_handler(exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
