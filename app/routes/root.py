import os
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

# Create a new router for the root endpoints
root_router = APIRouter()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="/app/public")


# Root endpoint - Serves the index.html file with root_path
@root_router.get("/", include_in_schema=False)
async def root(request: Request):
    root_path = os.getenv("ROOT_PATH", "")
    return templates.TemplateResponse(
        "index.html", {"request": request, "root_path": root_path}
    )
