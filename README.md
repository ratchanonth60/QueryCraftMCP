# QueryCraftMCP

QueryCraftMCP is a flexible Model Context Protocol (MCP) server designed to bridge the gap between Large Language Models (LLMs) and various database systems. It allows LLMs or other MCP clients to dynamically discover database schemas, execute queries, and retrieve data through a standardized protocol. The server supports multiple database backends (currently PostgreSQL and SQLite), selectable via configuration.

## Features

* **Multi-Database Backend Support:**
    * **PostgreSQL:** Asynchronous interaction using `asyncpg`, including connection pooling via lifespan management.
    * **SQLite:** Synchronous interaction using the built-in `sqlite3` library.
    * Easily configurable active backend using the `ACTIVE_DB_BACKEND` environment variable.
* **Dynamic Tool Loading:** Tools and database connection lifespans are dynamically loaded based on the configured backend.
* **Comprehensive Database Interaction Tools:**
    * **Schema Discovery:** Tools to list available databases (PostgreSQL), database objects (tables/views) (PostgreSQL), and object columns (PostgreSQL). For SQLite, a tool to retrieve the full table DDL schema is provided.
    * **Data Querying:**
        * Structured search capabilities (e.g., `search_data` for PostgreSQL).
        * Raw SQL query execution (e.g., `execute_raw_sql` for PostgreSQL, `execute_query` for SQLite) with security considerations.
* **Lifespan Management:** Robust management of database connections throughout the application lifecycle.
* **Transport Protocol:** Utilizes Server-Sent Events (SSE) for MCP communication.
* **Configuration:** Primarily through `.env` file and environment variables.
* **Docker Support:** Includes a `Dockerfile` (suggested in discussion, not uploaded) for easy containerization and deployment.

## Project Structure

The project follows a `src/` layout, with database-specific implementations organized under `src/db_backends/`:

```
QueryCraftMCP/
├── src/
│   ├── init.py
│   ├── main.py                 # Main application entry point
│   │
│   └── db_backends/
│       ├── init.py
│       ├── postgres/           # PostgreSQL specific modules
│       │   ├── init.py
│       │   ├── lifespan.py
│       │   ├── schema_tools.py
│       │   └── query_tools.py
│       └── sqlite/             # SQLite specific modules
│           ├── init.py
│           ├── lifespan.py

│           ├── schema_tools.py
│           └── query_tools.py
│
├── .env                        # For local environment variables
├── requirements.txt

├── Dockerfile                  # For building Docker images (example provided in discussion)
└── .dockerignore               # Specifies files to ignore in Docker build (example provided in discussion)
└── README.md
```


## Prerequisites

* Python 3.9+
* Docker (if running via Docker)
* Access to a PostgreSQL server (if using the PostgreSQL backend)
* A writable directory for the SQLite database file (if using the SQLite backend)

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd QueryCraftMCP
    ```

2.  **Create a Virtual Environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate    # On Windows
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    The dependencies include `mcp[cli]`, `asyncpg`, and `python-dotenv`.

4.  **Configure Environment Variables:**
    Create a `.env` file in the project root. Populate it with the necessary configurations:

    ```env
    # .env

    # --- General Configuration ---
    # Choose the active database backend: "postgres" or "sqlite"
    ACTIVE_DB_BACKEND="postgres"

    # MCP Server Host and Port (used by main.py)
    MCP_HOST="0.0.0.0"
    MCP_PORT="8888" # The port your MCP server will listen on with SSE/HTTP

    # --- PostgreSQL Backend Configuration ---
    # Required if ACTIVE_DB_BACKEND is "postgres"
    POSTGRES_DATABASE_URL="postgresql://your_user:your_password@your_pg_host:5432/your_database"

    # --- SQLite Backend Configuration ---
    # Required if ACTIVE_DB_BACKEND is "sqlite"
    # This path is relative to where the application runs.
    # If running in Docker, this path will be inside the container.
    SQLITE_DATABASE_PATH="querycraft_data.db"
    ```
    * Replace placeholder values (like `your_user`, `your_password`, etc.) with your actual credentials and paths.
    * The `MCP_HOST` and `MCP_PORT` are used by `FastMCP` when it's instantiated in `main.py`.

## Running the Application

### 1. Locally (Directly with Python)

Ensure your `.env` file is configured correctly.

```bash
python -m src.main
```

The server will start using the configured ACTIVE_DB_BACKEND and will listen on the host and port specified by MCP_HOST and MCP_PORT (defaulting to 0.0.0.0:8888) using SSE transport.

2. Using Docker
First, build the Docker image (assuming you have a Dockerfile like the one suggested in prior discussions):

```bash
docker build -t querycraftmcp .
```
Then, run the Docker container. You'll need to pass the environment variables.

Example for PostgreSQL Backend:
```bash
docker run -it --rm \
  -p 8888:8888 \
  -e ACTIVE_DB_BACKEND="postgres" \
  -e POSTGRES_DATABASE_URL="postgresql://docker_user:docker_pass@host.docker.internal:5432/docker_db" \
  -e MCP_HOST="0.0.0.0" \
  -e MCP_PORT="8888" \
  querycraftmcp
```
- Replace docker_user, docker_pass, docker_db with your actual PostgreSQL credentials.
- host.docker.internal can be used to connect to a PostgreSQL server running on your host machine from within the Docker container (on Docker Desktop for Mac/Windows).
- ```-p 8888:8888``` maps the host's port to the container's port.

