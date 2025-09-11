<p align="center">
  <img src="v-gpt-email-api.png" width="60%" alt="project-logo">
</p>
<p align="center">
    <h1 align="center">V-GPT-EMAIL-API</h1>
</p>
<p align="center">
    <em>Effortless Email Automation with Intelligent Precision</em>
</p>
<p align="center">
	<!-- local repository, no metadata badges. -->
<p>
<p align="center">
		<em>Developed with the software and tools below.</em>
</p>
<p align="center">
	<img src="https://img.shields.io/badge/Pydantic-E92063.svg?style=flat-square&logo=Pydantic&logoColor=white" alt="Pydantic">
	<img src="https://img.shields.io/badge/HTML5-E34F26.svg?style=flat-square&logo=HTML5&logoColor=white" alt="HTML5">
	<img src="https://img.shields.io/badge/YAML-CB171E.svg?style=flat-square&logo=YAML&logoColor=white" alt="YAML">
	<img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat-square&logo=Python&logoColor=white" alt="Python">
	<img src="https://img.shields.io/badge/AIOHTTP-2C5BB4.svg?style=flat-square&logo=AIOHTTP&logoColor=white" alt="AIOHTTP">
	<img src="https://img.shields.io/badge/Docker-2496ED.svg?style=flat-square&logo=Docker&logoColor=white" alt="Docker">
	<img src="https://img.shields.io/badge/FastAPI-009688.svg?style=flat-square&logo=FastAPI&logoColor=white" alt="FastAPI">
</p>

<br><!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary><br>

- [📍 Overview](#-overview)
- [🧩 Features](#-features)
- [📦 Modules](#-modules)
- [🚀 Getting Started](#-getting-started)
  - [⚙️ Installation](#️-installation)
  - [🤖 Usage](#-usage)
    - [From `docker-compose`](#from-docker-compose)
- [🛠 Project Changelog](#-project-changelog)
- [🎗 License](#-license)
</details>
<hr>

## 📍 Overview

The v-gpt-email-api is a sophisticated email management system designed to enhance productivity by integrating GPT-powered functionalities. It facilitates intelligent email handling, including drafting responses, sorting, and automating common tasks based on user preferences and historical data. Built with FastAPI and containerized through Docker, the API ensures secure and compliant email transmission, with robust validation and error-handling mechanisms. Its primary value lies in streamlining user workflows and personalizing email interactions, making it a valuable tool for efficient and intelligent email management in modern work environments.

---

## 🧩 Features

|    |   Feature         | Description |
|----|-------------------|---------------------------------------------------------------|
| ⚙️  | **Architecture**  | The project follows a microservices architecture, utilizing FastAPI with Uvicorn for handling asynchronous API requests, optimized using Docker to ensure isolated environments. This setup supports modular component integration. |
| 🔩 | **Code Quality**  | The code adheres to modern Python standards with strong type annotations, consistent naming conventions, and comprehensive function documentation, ensuring readability and maintainability. |
| 📄 | **Documentation** | Comprehensive documentation including a `README` file, inline comments, and docstrings. Key project files like `requirements.txt`, `Dockerfile`, and `docker-compose.yml` are well-documented to assist in deployment and integration. |
| 🔌 | **Integrations**  | Integrates key libraries such as FastAPI, Uvicorn, Pydantic for data validation, aiosmtplib for email, and aiohttp for HTTP requests. Environment variables managed using `python-dotenv`. Docker integration for containerization. |
| 🧩 | **Modularity**    | The codebase is highly modular with separate files for dependencies, models, and routes, facilitating reusability and easy maintenance. Logical separation of concerns across the application layers. |
| ⚡️  | **Performance**   | High efficiency and performance due to asynchronous programming with FastAPI and Uvicorn. Docker ensures optimized resource usage by providing isolated environments. |
| 🛡️ | **Security**      | Uses environment variables for sensitive configurations, API key validation for access control, and enforces file size and type constraints. Prioritizes secure email transmission and data protection. |
| 📦 | **Dependencies**  | Key dependencies include `aiohttp`, `pydantic`, `uvicorn`, `fastapi`, `aiosmtplib`, `python-dotenv`, and `aiofiles`. Managed using `requirements.txt` for easy installation and updates. |
| 🚀 | **Scalability**   | Designed for scalability with Docker and FastAPI. Can handle increased load efficiently due to asynchronous request handling and container orchestration capabilities provided by Docker Compose. |
```

---

## 🗂️ Repository Structure

```sh
└── v-gpt-email-api/
    ├── .env.example
    ├── Dockerfile
    ├── LICENSE
    ├── README.md
    ├── app
    │   ├── __init__.py
    │   ├── dependencies.py
    │   ├── main.py
    │   ├── models.py
    │   ├── routes
    │   │   ├── __init__.py
    │   │   ├── read_email.py
    │   │   └── send_email.py
    │   └── services
    │       ├── __init__.py
    │       └── imap_client.py
    ├── config
    │   └── signature.txt
    ├── docker-compose.yml
    ├── requirements.txt
    └── tests
        ├── test_dependencies.py
        ├── test_imap_client.py
        └── test_read_email.py
```

---

## 📦 Modules

| Path | Summary |
| --- | --- |
| [`app/`](app) | Core application code including API routes and IMAP services. |
| [`config/`](config) | Configuration resources such as the customizable `signature.txt`. |
| [`tests/`](tests) | Unit tests covering dependencies, IMAP client, and email routes. |
| [`docker-compose.yml`](docker-compose.yml) | Container orchestration for local deployment. |
| [`requirements.txt`](requirements.txt) | Python dependencies required by the service. |

<details closed><summary>app.routes</summary>

| File | Summary |
| --- | --- |
| [send_email.py](app/routes/send_email.py) | API endpoint for sending emails with validation and error handling. |
| [read_email.py](app/routes/read_email.py) | Endpoints for listing folders, retrieving messages, and handling IMAP actions. |

</details>

<details closed><summary>app.services</summary>

| File | Summary |
| --- | --- |
| [imap_client.py](app/services/imap_client.py) | Async helpers for interacting with the IMAP server to list, move, delete, and append messages. |

</details>

## 🚀 Getting Started

**System Requirements:**

* **Python**: `version 3.10`


### ⚙️ Installation

1. **Download the `docker-compose.yml` file**:  
   Save the provided `docker-compose.yml` file to your project directory.

2. **Edit Environment Variables**:  
   Open the `docker-compose.yml` file and set the environment variables according to your setup:

    ```yaml
    environment:
      BASE_URL: https://api.servicesbyv.com  # Set this to your actual base URL
      ROOT_PATH: /email
      API_KEY: "Optional API key to connect to api"
      WORKERS: 1  # uvicorn workers 1 should be enough for personal use
      UVICORN_CONCURRENCY: 32  # this controls the max connections. Anything over the API_concurrency value is queued and excess rejected.
      ACCOUNT_EMAIL: user1@example.com
      ACCOUNT_PASSWORD: password1
      ACCOUNT_IMAP_SERVER: imap.example.com
      ACCOUNT_IMAP_PORT: 993
      ACCOUNT_SMTP_SERVER: smtp.example.com
      ACCOUNT_SMTP_PORT: 587
      ACCOUNT_REPLY_TO: replyto@example.com
    ```

    The service validates the SMTP settings on startup. Ensure `ACCOUNT_EMAIL`,
    `ACCOUNT_PASSWORD`, `ACCOUNT_SMTP_SERVER`, and `ACCOUNT_SMTP_PORT` are set
    or the application will raise a runtime error at launch.

3. **Run the Docker Compose**:  
   Use the following command to start the service:

   ```bash
   docker-compose up
   ```

4. **(Optional) Run in Detached Mode**:
   To run the containers in the background, use:

   ```bash
   docker-compose up -d
   ```

### Environment Variables

| Name | Default | Description |
| --- | --- | --- |
| `FROM_NAME` | *(empty)* | Display name used in outgoing emails. |
| `ATTACHMENT_CONCURRENCY` | `3` | Number of attachments processed in parallel. |
| `START_TLS` | `True` | Enables STARTTLS for SMTP connections. |

The email signature appended to outbound messages can be customized in [`config/signature.txt`](config/signature.txt).

### 🤖 Usage

#### From `docker-compose`

1. **Access the OpenAPI Specifications**:  
   To get the OpenAPI specifications and integrate with your AI tool, navigate to:

   ```
   BASE_URL/openapi.json
   ```

   Replace `BASE_URL` with the actual URL of your application (e.g., `https://api.servicesbyv.com/email/openapi.json`).

2. **Available IMAP Endpoints**:

   | Method & Path | Description |
   | --- | --- |
   | `GET /folders` | List available mailboxes. |
   | `GET /emails` | Retrieve messages from a folder with optional `limit`, `unread`, and `folder` query parameters. |
   | `POST /emails/{uid}/move` | Move an email to another folder via the `folder` query parameter. |
   | `POST /emails/{uid}/forward` | Forward a message using the same payload as the send endpoint. |
   | `POST /emails/{uid}/reply` | Reply to a message using the same payload as the send endpoint. |
   | `DELETE /emails/{uid}` | Delete a message from a folder (defaults to `INBOX`). |
   | `POST /drafts` | Store a draft message in the "Drafts" folder. |

---

## 🛠 Project Changelog

See [CHANGELOG.md](CHANGELOG.md) for a full history of updates, including recent documentation improvements.

---

## 🎗 License

This project is protected under the MIT Licence

---

[**Return**](#-overview)

---
