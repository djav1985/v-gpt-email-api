# main,py
import os

from fastapi import FastAPI

from routes.send_email import send_router


# FastAPI application instance setup
app = FastAPI(
    title="Email Management API",
    version="0.1.0",
    description="A FastAPI to send emails",
    openapi_prefix=os.getenv('ROOT_PATH', '/'),
    servers=[{"url": f"{os.getenv('BASE_URL', '')}{os.getenv('ROOT_PATH', '/')}", "description": "Base API server"}]
)

# Include routers for feature modules
app.include_router(send_router)
