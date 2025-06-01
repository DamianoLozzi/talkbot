# TalkBot

**TalkBot** is a Python application that monitors Talk chats on Nextcloud and sends/receives messages via Ollama. With Docker and Docker Compose, you can start the bot in a few commands without exposing credentials in the repository.

---

## Table of Contents

1. [Description](#description)
2. [Prerequisites](#prerequisites)
3. [Project Structure](#project-structure)
4. [Configuration](#configuration)

   * 4.1. `.env.example` File
5. [Running Locally (without Docker)](#running-locally-without-docker)
6. [Running with Docker](#running-with-docker)

   * 6.1. Building the Image
   * 6.2. Using `docker run`
   * 6.3. Using Docker Compose
7. [Main Files](#main-files)
8. [Log Management](#log-management)
9. [License](#license)

---

## 1. Description

TalkBot is a Python bot that:

* **Monitors** Talk chats on Nextcloud where at least one message has been sent to the bot.
* **Communicates** with an Ollama instance to generate and receive AI-driven responses.
* **Uses Nextcloud storage** to save necessary data for its functionality.
* **Logs** events and messages in both plain text and JSON formats inside a `logs/` directory.

Architecture components:

1. **nextcloud\_client**: connects and authenticates to Nextcloud as a dedicated bot user, polls active Talk chats, and fetches new messages.
2. **ollama\_client**: sends requests to the Ollama HTTP API and receives model responses.
3. **TalkBot (main)**: orchestrates the workflow: Nextcloud → Ollama → Nextcloud (or local output).

---

## 2. Prerequisites

Before running TalkBot, ensure you have:

* **Docker Engine** (version 20.10+ recommended)
* **Docker Compose** (version 1.29+ or Compose V2)
* (Optional) **Python 3.10+** if you want to run the bot locally without Docker
* An accessible **Nextcloud** instance with a dedicated bot user (credentials for this user will be used by TalkBot).
* An accessible **Ollama** instance via HTTP (host\:port).

---

## 3. Project Structure

```text
talkbot/
├── Dockerfile
├── docker-compose.yml
├── config_template.ini      # Template showing required settings
├── .env.example             # Example with environment variables (explanatory comments)
├── .gitignore
├── README.md
├── requirements.txt
├── talkbot.py               # Main entry point
├── lib/
│   ├── config.py            # Loads settings from ENV or config.ini
│   ├── constants.py
│   ├── message_processor.py
│   ├── nextcloud_client.py  # Renamed from nextcloud_bot.py
│   ├── ollama_client.py     # Renamed from ollama_chat.py
│   └── retry.py
└── logs/                    # Mounted directory for runtime logs
```

All sensitive credentials (API keys, passwords, host URLs, etc.) are read from environment variables. The `.env.example` file shows exactly which variables need to be set.

---

## 4. Configuration

### 4.1. `.env.example` File

Copy the example file and replace the explanatory comments with your actual values. **Do not commit** the `.env` file that contains real secrets.

```dotenv
# Example .env.example file

# Nextcloud settings (dedicated bot user)
NEXTCLOUD_URL=             # e.g. https://your-nextcloud.server/nextcloud
NEXTCLOUD_USERNAME=        # Username of the bot user
NEXTCLOUD_PASSWORD=        # Password of the bot user
# NEXTCLOUD_MAX_RETRIES=   # (Optional) Number of retry attempts on failure (default: 5)
# NEXTCLOUD_RETRY_DELAY=   # (Optional) Delay between retries in seconds (default: 2)
# NEXTCLOUD_CHECK_INTERVAL=# (Optional) Polling interval in seconds (default: 5)
# NEXTCLOUD_BACKOFF=       # (Optional) Exponential backoff factor (default: 1.2)

# Ollama settings
OLLAMA_HOST=               # e.g. http://your-ollama.server:11434
OLLAMA_MODEL=              # e.g. llama3.1
OLLAMA_SYSTEM_PROMPT=      # System prompt text defining the bot’s persona
OLLAMA_ACTOR_ID=           # Actor/username used when sending messages

# Logging settings
LOG_DIRECTORY=./logs       # Directory for log files (can remain ./logs)
LOG_FILENAME=              # Plain text log filename (e.g., talkbot.log)
JSON_LOG_FILENAME=         # JSON-formatted log filename (e.g., talkbot.json)
CONSOLE_COLORIZE=1         # 1 to enable colored console output, 0 to disable
LOG_COLORIZE=0             # 1 to colorize file logs, 0 to disable
JSON_COLORIZE=0            # 1 to colorize JSON logs, 0 to disable
LOG_LEVEL=DEBUG            # Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_FORMAT=%(asctime)s.%(msecs)03d | %(filename)s:%(lineno)d | %(levelname)s | %(message)s
DATE_FORMAT=%Y-%m-%d %H:%M:%S
```

> **Note**: All variables without default values are **required**; missing a required variable will cause the bot to throw an error.

---

## 5. Running Locally (without Docker)

1. Install Python 3.10+ and create a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Export environment variables according to your `.env` (or create a `config.ini` based on `config_template.ini`).
4. Start the bot:

   ```bash
   python talkbot.py
   ```

   The bot will start monitoring Talk chats on Nextcloud, send/receive messages via Ollama, and save logs in `./logs/`.

---

## 6. Running with Docker

### 6.1. Building the Image

From the project root, run:

```bash
docker build -t talkbot:latest .
```

This does the following:

* Uses `python:3.10-slim` as a base image.
* Installs `git` and Python dependencies.
* Copies source code into `/app` and creates `/app/logs`.

### 6.2. Using `docker run`

To run the bot without Docker Compose:

```bash
docker run -d \
  --name talkbot-container \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  talkbot:latest
```

* `--env-file .env` loads all environment variables defined in `.env`.
* `-v $(pwd)/logs:/app/logs` mounts the log directory on the host.
* By default, the restart policy is `no` (it won’t restart automatically).

To enable automatic restart on crash or host reboot, add:

```bash
  --restart unless-stopped
```

### 6.3. Using Docker Compose

A `docker-compose.yml` file is provided for simpler startup. Just run:

```bash
docker-compose up -d
```

What happens:

* Compose builds (if needed) the `talkbot:latest` image using the `Dockerfile`.
* Launches a container named `talkbot`:

  * All environment variables are loaded from `.env`.
  * The local `./logs` directory is mounted to `/app/logs`.
  * The restart policy is set to `unless-stopped`.
  * Networking is configured (bridge mode by default).

To view logs in real time:

```bash
docker-compose logs -f talkbot
```

To stop and remove containers:

```bash
docker-compose down
```

---

## 7. Main Files

* **`talkbot.py`**:
  Entry point that initializes `Config()`, sets up `nextcloud_client` and `ollama_client`, and starts the main polling loop.

* **`lib/config.py`**:
  Singleton `Config` class that reads settings from environment variables (or a local `config.ini` if present). Uses `RawConfigParser` to avoid interpolation errors with `%` in log formats.

* **`lib/nextcloud_client.py`**:
  Logic to authenticate with Nextcloud as a dedicated bot user, monitor Talk chats, fetch new messages, and store data as needed.

* **`lib/ollama_client.py`**:
  Wraps HTTP calls to the Ollama `/chat` endpoint. Implements retry using the helpers from `lib/retry.py`.

* **`lib/retry.py`**:
  Provides decorators for synchronous and asynchronous retry with exponential backoff.

* **`lib/message_processor.py`**:
  Processes incoming messages from Nextcloud, formats them, sends them to `ollama_client`, and logs results.

* **`lib/constants.py`**:
  Defines static constants (emoji sets, supported file types, default headers, etc.).

---

## 8. Log Management

* All logs (plain text and JSON) are saved in `./logs/` both locally and inside the container.
* Log filenames are defined by `LOG_FILENAME` (e.g., `talkbot.log`) and `JSON_LOG_FILENAME` (e.g., `talkbot.json`).
* You can configure log level, formats, and colorization via environment variables.
* In Docker, the volume mount `./logs:/app/logs` ensures logs persist even if the container is recreated.

---

## 9. License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

*End of README*
