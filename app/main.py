# main,py
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routes.send_email import send_router
from routes.root import root_router

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
app.include_router(root_router)

# Serve static files (HTML, CSS, JS, images)
app.mount("/static", StaticFiles(directory="/app/public"), name="static")
