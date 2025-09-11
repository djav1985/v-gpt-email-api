# main,py
import os
import aiofiles
from fastapi import FastAPI

from . import dependencies
from .routes.send_email import send_router
from .routes.read_email import read_router


openapi_tags = [
    {"name": "Send", "description": "Endpoints for sending emails"},
    {"name": "Read", "description": "Endpoints for reading emails"},
]


# FastAPI application instance setup
app = FastAPI(
    title="Email Management API",
    version="0.1.0",
    description="A FastAPI to send emails",
    contact={"name": "API Support", "email": "support@example.com"},
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    terms_of_service="https://example.com/terms/",
    openapi_tags=openapi_tags,
    root_path=os.getenv('ROOT_PATH', '/'),
    root_path_in_servers=False,
    servers=[
        {
            "url": f"{os.getenv('BASE_URL', '')}{os.getenv('ROOT_PATH', '/')}",
            "description": "Base API server",
        }
    ]
)


@app.on_event("startup")
async def startup_event() -> None:
    dependencies.settings = dependencies.Config()
    try:
        async with aiofiles.open("config/signature.txt", "r") as file:
            dependencies.signature_text = await file.read()
    except FileNotFoundError:
        dependencies.signature_text = ""


# Include routers for feature modules
app.include_router(send_router)
app.include_router(read_router)
