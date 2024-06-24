# main,py
import os

from fastapi import FastAPI

from routes.send_email import send_router


# FastAPI application instance setup
app = FastAPI(
    title="Email Management API",
    version="0.1.0",
    description="A FastAPI to send emails",
    root_path=os.getenv("ROOT_PATH", ""),
    servers=[{"url": os.getenv("BASE_URL", ""), "description": "Base API server"}],
)

# Include routers for feature modules
app.include_router(send_router)
