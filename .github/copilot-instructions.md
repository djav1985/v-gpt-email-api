
# Copilot Instructions for v-gpt-email-api

## Project Overview
- FastAPI microservice for GPT-powered email automation: drafting, sorting, and automating email tasks.
- Containerized via Docker; orchestrated with `docker-compose.yml`.
- Key dependencies: FastAPI, Uvicorn, Pydantic, aiosmtplib, aiohttp, python-dotenv, aiofiles.

## Architecture & Key Files
- Main entrypoint: `app/main.py` (initializes FastAPI, includes routers from `app/routes/`).
- API endpoints: `app/routes/send_email.py` (send), `app/routes/read_email.py` (read); add new endpoints in `app/routes/` and register in `main.py`.
- Email logic: `app/dependencies.py` (dependency injection, validation), `app/models.py` (Pydantic models for email data).
- IMAP/SMTP integration: `app/services/imap_client.py` (IMAP logic), aiosmtplib for SMTP.
- Configuration: All sensitive config (SMTP/IMAP credentials, API key, concurrency) loaded from environment variables via `docker-compose.yml`.

## Developer Workflows
- **Build & Run:**
  - Use `docker-compose up` to build and run the service. For detached mode: `docker-compose up -d`.
  - Do not run with `uvicorn` directly unless debugging locally.
- **Testing:**
  - Run unit tests in `tests/` (e.g., `pytest tests/`).
  - Test coverage includes edge cases (see `AGENTS.md`).
- **Linting:**
  - Use project linters/formatters before committing (see `AGENTS.md`).
- **API Docs:**
  - OpenAPI spec at `/openapi.json` when service is running.

## Patterns & Conventions
- **Modularity:**
  - Business logic separated into dependencies, models, routes, and services for maintainability.
  - Dependency injection for API key validation and email sending (see `app/dependencies.py`).
- **Validation & Security:**
  - Pydantic models strictly validate all email data (`app/models.py`).
  - API key required for all endpoints; validated via dependency injection.
  - File size/type constraints enforced for attachments.
- **Async Operations:**
  - All I/O (email, HTTP, file) is asynchronous for performance.
- **Error Handling:**
  - Use FastAPI's exception system and custom validation logic.

## Integration Points
- **External Email Services:**
  - SMTP via aiosmtplib; IMAP via custom logic in `app/services/imap_client.py`.
- **Environment Variables:**
  - All credentials/config loaded from environment (see `docker-compose.yml`).
- **Docker:**
  - Service is always run in a container; direct `uvicorn` usage only for local debugging.

## Examples
- Add new API endpoint: create a router in `app/routes/`, register in `main.py`.
- Change email validation: update Pydantic models in `app/models.py`.
- Update SMTP/IMAP settings: edit environment variables in `docker-compose.yml`.

## References
- See `README.md` for setup and module documentation.
- See `AGENTS.md` for contributor/test/linting expectations.
- Key files: `app/main.py`, `app/dependencies.py`, `app/models.py`, `app/routes/send_email.py`, `app/services/imap_client.py`, `docker-compose.yml`, `Dockerfile`, `requirements.txt`.

---

If any section is unclear or incomplete, please provide feedback for further refinement.