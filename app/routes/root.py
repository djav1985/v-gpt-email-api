# routes/root.py
from fastapi import APIRouter
from starlette.responses import FileResponse

# Create a new router for the root endpoints
root_router = APIRouter()


# Root endpoint - Serves the index.html file
@root_router.get("/", include_in_schema=False)
async def root():
    return FileResponse("/app/public/index.html")


@root_router.get("/profile.png", include_in_schema=False)
async def profile():
    return FileResponse("/app/public/profile.png")


@root_router.get("/brushed-alum.png", include_in_schema=False)
async def brushedalum():
    return FileResponse("/app/public/brushed-alum.png")


@root_router.get("/glass.png", include_in_schema=False)
async def rglass():
    return FileResponse("/app/public/glass.png")
