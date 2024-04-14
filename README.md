# v-gpt-email-api 

## Overview
This FastAPI application provides robust email management capabilities, allowing users to interact with their email accounts for various functionalities like listing folders, reading, sending, and organizing emails.

## Features
- **List Email Folders**: Retrieve all folders from an email account.
- **List Emails**: Fetch emails from a specified folder.
- **Read Emails**: Get detailed information about specific emails.
- **Send Emails**: Compose and send emails from a specified account.
- **Move Emails**: Move emails between folders.
- **Reply to Emails**: Send replies to received emails.

## Installation

### Prerequisites
- Docker
- Python 3.10+
- pip

### Clone the Repository
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### Environment Setup
Create a `.env` file at the root of your project directory and populate it with necessary environment variables:

```makefile
BASE_URL=http://localhost
API_KEY=your_api_key
ACCOUNTS='[{"email": "user1@example.com", "password": "password1", "imap_server": "imap.example.com", "imap_port": 993, "smtp_server": "smtp.example.com", "smtp_port": 587}, {"email": "user2@example.com", "password": "password2", "imap_server": "imap.example2.com", "imap_port": 993, "smtp_server": "smtp.example2.com", "smtp_port": 587}]'
```

### Build and Run with Docker
```bash
docker-compose up --build
```

## Usage
Once the application is running, you can interact with the API through the following endpoints:

### API Endpoints

#### List Folders
- **POST /list_folders**
- Description: Lists all folders in the specified email account.
- Payload:
```json
{
  "account": "user@example.com"
}
```

#### List Emails
- **POST /list_emails**
- Description: Lists emails from a specified folder.
- Payload:
```json
{
  "account": "user@example.com",
  "folder": "Inbox",
  "limit": 10
}
```

#### Read Emails
- **POST /read_emails**
- Description: Retrieves detailed information about specified emails.
- Payload:
```json
{
  "account": "user@example.com",
  "folder": "Inbox",
  "email_ids": "1,2,3"
}
```

#### Send Email
- **POST /send_email**
- Description: Sends an email from the specified account.
- Payload:
```json
{
  "account": "user@example.com",
  "to_address": "receiver@example.com",
  "subject": "Hello",
  "body": "Hello, this is a test email."
}
```

#### Move Emails
- **POST /move_emails**
- Description: Moves specified emails to a different folder.
- Payload:
```json
{
  "account": "user@example.com",
  "folder": "Inbox",
  "email_ids": "4,5",
  "target_folder": "Archived"
}
```

#### Reply to Email
- **POST /reply_email**
- Description: Sends a reply to an email.
- Payload:
```json
{
  "account": "user@example.com",
  "folder": "Inbox",
  "email_id": "6",
  "reply_body": "Thanks for your email."
}
```
