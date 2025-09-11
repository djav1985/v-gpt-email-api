# Changelog

All notable changes to this project will be documented in this file.
See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [Unreleased]
### Added
- IMAP configuration (`ACCOUNT_IMAP_SERVER`, `ACCOUNT_IMAP_PORT`).
- IMAP utilities and API endpoints for listing folders, fetching, moving, forwarding, replying, deleting, and drafting emails.
- Dedicated `imap` router consolidating IMAP operations.
- Support for moving emails from arbitrary source folders.
- Forward and reply endpoints now reuse the original message and set threading headers.
- Mailbox parsing handles quoted names and spaces.
- Header decoding concatenates multi-part encodings.
- Attachment downloads restricted to HTTP/HTTPS schemes.
- Email summary dates stored as `datetime` and serialized in ISO format.
- Send/Read tags added to the FastAPI application.
- Consistent `MessageResponse` model used across message endpoints and documented error responses.
- Named API key bearer security scheme exposed in the OpenAPI schema.
- Tests for API key validation and email sending error handling.
- Extensive tests for dependencies, IMAP client, routes, models, and startup logic.
- `account_reply_to` configuration option for customizing the Reply-To header.
- Validation for required fields in email models, including recipient lists, subjects, bodies, messages, UIDs, and attachment URLs.
- Standardized `ErrorResponse` model with example payloads and documented 401/403 responses.
- Example request bodies and success responses for email routes and models.
- OpenAPI metadata now declares version 3.1.0 and derives the server URL from `BASE_URL` and `ROOT_PATH` environment variables.
- Streaming attachment downloads to disk to limit memory usage.
- Added `requirements-dev.txt` with `pytest` and `pytest-asyncio`, and documented test execution steps.
- `FoldersResponse` and `EmailBody` models for structured folder and body responses.
- `ErrorCode` enumeration for standardized error codes.

### Changed
- Routes and IMAP client now reference settings dynamically via `dependencies.settings`.
- Explicit operation IDs defined for read email endpoints.
- `send_email` accepts a list of attachment URLs via `file_urls` instead of a comma-separated string.
- API routes now use `Security(get_api_key)` for API-key protection and include descriptive OpenAPI tags.
- Send email endpoint now returns HTTP 201 on success.
- Forwarding emails respect the provided request body.
- `limit` query parameters on email listing routes must be positive.
- Console prints replaced with structured logging; logging configuration is now left to the host environment.
- Startup now validates required environment variables before initializing settings.
- Folder listing endpoints now return `FoldersResponse` instead of a raw list.
- `Config` now uses `BaseSettings` for environment loading and is instantiated directly.
- `EmailSummary.from_` validated as `EmailStr`.
- Shared IMAP operations consolidated into reusable helpers.
- API key retrieval and HTTP exception handling are now synchronous.
- Forward and reply endpoints accept an optional folder parameter.
- Tests use `pytest.mark.asyncio` instead of `asyncio.run`.
- Removed blanket `flake8` ignores in favor of targeted suppressions.
- `SendEmailRequest.file_url` renamed to `file_urls`.
- Attachment filenames are sanitized and path traversal is blocked.
- `get_api_key` now requires a Bearer token and rejects missing credentials.
- Invalid SMTP or IMAP port values raise a descriptive `RuntimeError`.
- Temporary attachment directories are removed in a background thread to avoid blocking.

### Removed
- Deprecated `app/services/imap_client.py` in favor of a dedicated IMAP router.
