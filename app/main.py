# main,py
import os
import aiofiles
from fastapi import FastAPI, Request, HTTPException
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


# FastAPI application instance setup
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    dependencies.settings = dependencies.Config(
        account_email=os.getenv("ACCOUNT_EMAIL") or "",
        account_password=os.getenv("ACCOUNT_PASSWORD") or "",
        account_smtp_server=os.getenv("ACCOUNT_SMTP_SERVER") or "",
        account_smtp_port=int(os.getenv("ACCOUNT_SMTP_PORT", "587")),
        account_imap_server=os.getenv("ACCOUNT_IMAP_SERVER") or "",
        account_imap_port=int(os.getenv("ACCOUNT_IMAP_PORT", "993")),
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
    root_path=os.getenv('ROOT_PATH', '/'),
    root_path_in_servers=False,
    servers=[
        {
            "url": f"{os.getenv('BASE_URL', '')}{os.getenv('ROOT_PATH', '/')}",
            "description": "Base API server",
        }
    ],
    lifespan=lifespan
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
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
