import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes.send_email import send_router
from routes.list_email import list_router
from routes.read_email import read_router
from routes.move_email import move_router
from routes.root import root_router

# FastAPI application instance setup
app = FastAPI(
    title="Email Management API",
    version="0.1.0",
    description="A FastAPI application that manages email accounts",
    servers=[{"url": os.getenv("BASE_URL", ""), "description": "Base API server"}]
)

# Include routers for feature modules
app.include_router(send_router)
app.include_router(list_router)
app.include_router(read_router)
app.include_router(move_router)
app.include_router(root_router)

# Serve static files (HTML, CSS, JS, images)
app.mount("/static", StaticFiles(directory="/app/public"), name="static")
