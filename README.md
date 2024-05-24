Email Management API
This project is an Email Management API built using FastAPI that allows users to send emails with optional file attachments via HTTP endpoints.

Features
Send Emails: Send emails to one or multiple recipients. You can also attach files to these emails by providing URLs to the files.
Static File Serving: Serve static files like HTML, CSS, and JavaScript from a specified directory.
API Key Authentication: Secure the email sending endpoint with an API key.
Project Structure
config.ts: Configuration modification function.
root.py: Handles the root endpoint to serve the index.html file.
send_email.py: Contains the endpoint and logic for sending emails.
dependencies.py: Helper functions and dependencies for sending emails.
main.py: Main FastAPI application setup and router inclusion.
models.py: Pydantic models for request validation.
.gitattributes: Configuration for Git to handle end-of-line normalization.
docker-compose.yml: Docker Compose configuration to run the application in a containerized environment.
Requirements
Docker
Docker Compose
Getting Started
Clone the repository:

git clone https://your-repository-url.git
cd your-repository-folder
Running the Application Locally
Use Docker Compose to build and run the application:

docker-compose up -d
The API will be available at http://localhost:8050.

Environment Variables
You need to set the following environment variables in the docker-compose.yml file:

BASE_URL: The base URL for the API.
API_KEY: API key for connecting to the API.
WORKERS: Uvicorn workers count.
UVICORN_CONCURRENCY: Maximum concurrent connections.
ACCOUNT_EMAIL: Email address for sending emails.
ACCOUNT_PASSWORD: Password for the email account.
ACCOUNT_SMTP_SERVER: SMTP server address.
ACCOUNT_SMTP_PORT: SMTP server port.
ACCOUNT_REPLY_TO: Reply-to email address.
File Attachments
Supported file types for attachments are:

.zip
.txt
.docx
.png
.webp
.jpg
.jpeg
.pdf
.rtf
The maximum attachment size is 20MB.

API Endpoints
Send Email
POST /send_email

Send an email with optional file attachments.

Request Body:

{
  "to_address": "recipient@example.com",
  "subject": "Email Subject",
  "body": "Email body content.",
  "file_url": [
    "https://example.com/file1.pdf",
    "https://example.com/file2.png"
  ]
}
Response:

{
  "message": "Email sent successfully"
}
Root Endpoint
GET /

Serves the index.html file.

License
This project is licensed under the MIT License.
