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
    ├── Dockerfile
    ├── LICENSE
    ├── README.md
    ├── app
    │   ├── __init__.py
    │   ├── dependencies.py
    │   ├── main.py
    │   ├── models.py
    │   ├── public
    │   └── routes
    ├── docker-compose.yml
    ├── images
    │   └── header.png
    └── requirements.txt
```

---

## 📦 Modules

<details closed><summary>.</summary>

| File                                     | Summary                                                                                                                                                                                                                                                                                                                                         |
| ---                                      | ---                                                                                                                                                                                                                                                                                                                                             |
| [requirements.txt](requirements.txt)     | Requirements.txt specifies the necessary dependencies for the application, including FastAPI for web framework, Uvicorn for ASGI server, Pydantic for data validation, aiosmtplib for SMTP client, aiohttp for asynchronous HTTP requests, aiofiles for file operations, and python-dotenv for environment variable management.                 |
| [docker-compose.yml](docker-compose.yml) | Configure the applications deployment environment, defining service parameters, environmental variables, and network settings. Enables containerized operation of the v-gpt-email-api, ensuring seamless integration and communication with email servers and APIs for the intended functionalities within the broader repository architecture. |
| [Dockerfile](Dockerfile)                 | Facilitates the deployment of the v-gpt-email-api repository by defining a multi-stage Docker build, installing dependencies, setting environment variables, and configuring the FastAPI application to run with Uvicorn. This ensures an optimized and isolated environment for running the API service efficiently.                           |

</details>

<details closed><summary>app</summary>

| File                                   | Summary                                                                                                                                                                                                                                                                                                                               |
| ---                                    | ---                                                                                                                                                                                                                                                                                                                                   |
| [main.py](app/main.py)                 | Main.py initializes the FastAPI application instance for the Email Management API, setting the application’s metadata and configuration. It integrates the email sending feature by including the appropriate router, enabling the API to handle email-sending requests within the repository’s architecture.                         |
| [dependencies.py](app/dependencies.py) | Facilitates email dispatching with file attachments, integrates API key validation, and fetches remote files. Utilizes environment variables for SMTP configuration, manages email signatures, and enforces file size and type constraints to ensure compliant and secure email transmission as part of the broader email API system. |
| [models.py](app/models.py)             | Define the structure for email-related data within the API, ensuring standardized validation and descriptive metadata for each email attribute. This facilitates consistent data handling and error checking across email functionalities in the repositorys broader email service architecture.                                      |

</details>

<details closed><summary>app.routes</summary>

| File                                      | Summary                                                                                                                                                                                                                                                                                                    |
| ---                                       | ---                                                                                                                                                                                                                                                                                                        |
| [send_email.py](app/routes/send_email.py) | Defines an API endpoint for sending emails, integrating request validation and error handling. Utilizes dependency injection for API key management and email sending functionality. Enhances the parent repositorys capability by providing a robust mechanism for email dispatch within the application. |

</details>

---

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

### 🤖 Usage

#### From `docker-compose`

1. **Access the OpenAPI Specifications**:  
   To get the OpenAPI specifications and integrate with your AI tool, navigate to:

   ```
   BASE_URL/openapi.json
   ```

   Replace `BASE_URL` with the actual URL of your application (e.g., `https://api.servicesbyv.com/email/openapi.json`).
   
---

## 🛠 Project Changelog

-  `► `
-  `► `
-  `► `

---

## 🎗 License

This project is protected under the MIT Licence

---

[**Return**](#-overview)

---
