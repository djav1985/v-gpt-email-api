# Copilot Instructions for v-gpt-email-api

## Project Overview
- This is a FastAPI-based microservice for intelligent email automation, using GPT-powered features for drafting, sorting, and automating email tasks.
- The service is containerized with Docker and orchestrated via `docker-compose.yml`.
- Key dependencies: FastAPI, Uvicorn, Pydantic, aiosmtplib, aiohttp, python-dotenv, aiofiles.

## Architecture & Key Files
- Main entrypoint: `app/main.py` (initializes FastAPI, includes routers)
- Email logic & validation: `app/dependencies.py`, `app/models.py`
- API endpoints: `app/routes/send_email.py` (uses dependency injection for API key and email sending)
- Configuration: Environment variables set in `docker-compose.yml` (SMTP/IMAP credentials, API key, concurrency)
- All sensitive config is loaded via environment variables, not hardcoded.

## Developer Workflows
- **Build & Run:**
  - Use `docker-compose up` to build and run the service (see README for details).
  - For background mode: `docker-compose up -d`
- **Environment Setup:**
  - Python 3.10 required.
  - SMTP/IMAP settings must be valid or the app will fail at startup.
- **API Documentation:**
  - OpenAPI spec available at `/openapi.json` (useful for AI agents and integration).

## Patterns & Conventions
- **Modularity:**
  - All business logic is separated into dependencies, models, and routes for maintainability.
  - Dependency injection is used for API key validation and email sending.
- **Validation & Security:**
  - Pydantic models enforce strict validation for all email data.
  - API key required for access; validated via dependency injection.
  - File size/type constraints enforced for attachments.
- **Error Handling:**
  - Errors are handled with FastAPI's exception system and custom validation logic.
- **Async Operations:**
  - All I/O (email, HTTP, file) is asynchronous for performance.

## Integration Points
- **External Email Services:**
  - Uses aiosmtplib for SMTP and aiohttp for remote file fetching.
- **Environment Variables:**
  - All credentials and config are loaded from environment (see `docker-compose.yml`).
- **Docker:**
  - Service is always run in a container; do not run directly with `uvicorn` unless debugging locally.

## Examples
- To add a new API endpoint, create a new file in `app/routes/`, define a router, and include it in `main.py`.
- To change email validation, update the Pydantic models in `app/models.py`.
- To update SMTP/IMAP settings, edit environment variables in `docker-compose.yml`.

## References
- See `README.md` for full setup and module documentation.
- Key files: `app/main.py`, `app/dependencies.py`, `app/models.py`, `app/routes/send_email.py`, `docker-compose.yml`, `Dockerfile`, `requirements.txt`.

---

If any section is unclear or missing, please provide feedback for further refinement.