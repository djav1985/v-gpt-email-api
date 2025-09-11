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
