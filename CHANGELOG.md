# Changelog

All notable changes to this project will be documented in this file.
See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [Unreleased]
### Added
- IMAP configuration (`ACCOUNT_IMAP_SERVER`, `ACCOUNT_IMAP_PORT`).
- IMAP utilities and API endpoints for listing folders, fetching, moving, forwarding, replying, deleting, and drafting emails.
- Support for moving emails from arbitrary source folders.
- Forward and reply endpoints now reuse the original message and set threading headers.
- Mailbox parsing handles quoted names and spaces.
- Header decoding concatenates multi-part encodings.
- Attachment downloads restricted to HTTP/HTTPS schemes.
- Email summary dates stored as `datetime` and serialized in ISO format.
- Contact, license, and terms metadata added to the FastAPI application along with Send/Read tags.
- Consistent `MessageResponse` model used across message endpoints and documented error responses.
- Named API key bearer security scheme exposed in the OpenAPI schema.
- Tests for API key validation and email sending error handling.
- Extensive tests for dependencies, IMAP client, routes, models, and startup logic.
- `account_reply_to` configuration option for customizing the Reply-To header.
- Validation for required fields in email models, including recipient lists, subjects, bodies, messages, UIDs, and attachment URLs.

### Changed
- Routes and IMAP client now reference settings dynamically via `dependencies.settings`.
- Explicit operation IDs defined for read email endpoints.
