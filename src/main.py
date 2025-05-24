import importlib
import os

from dotenv import load_dotenv
from mcp.server import FastMCP

# Load .env file for environment variables
load_dotenv()

# Determine the active database backend from environment variable
# Defaults to "postgres" if not set
ACTIVE_DB_BACKEND = os.environ.get("ACTIVE_DB_BACKEND", "postgres")

print(f"INFO: Active database backend configured: '{ACTIVE_DB_BACKEND}'")

# --- Dynamically import modules from the active backend ---
try:
    print(f"INFO: Importing lifespan and tools for '{ACTIVE_DB_BACKEND}' backend...")
    # Construct module paths
    lifespan_module_path = f"src.db_backends.{ACTIVE_DB_BACKEND}.lifespan"
    schema_tools_module_path = f"src.db_backends.{ACTIVE_DB_BACKEND}.schema_tools"
    query_tools_module_path = f"src.db_backends.{ACTIVE_DB_BACKEND}.query_tools"

    # Import modules
    lifespan_module = importlib.import_module(lifespan_module_path)
    schema_tools_module = importlib.import_module(schema_tools_module_path)
    query_tools_module = importlib.import_module(query_tools_module_path)

    # Get the lifespan function
    app_lifespan = lifespan_module.app_lifespan

    if ACTIVE_DB_BACKEND == "sqlite":
        tool_get_schema = getattr(schema_tools_module, "get_database_schema", None)
        tool_execute_query = getattr(query_tools_module, "execute_query", None)
        # เพิ่ม tools อื่นๆ ของ SQLite ตามต้องการ
    elif ACTIVE_DB_BACKEND == "postgres":
        # ดึง tools ของ postgres ตามเดิม
        tool_list_available_databases = getattr(
            schema_tools_module, "list_available_databases", None
        )
        tool_list_database_objects = getattr(
            schema_tools_module, "list_database_objects", None
        )
        tool_get_object_columns = getattr(
            schema_tools_module, "get_object_columns", None
        )
        tool_search_data = getattr(query_tools_module, "search_data", None)
        tool_execute_raw_sql = getattr(query_tools_module, "execute_raw_sql", None)

    print("INFO: Backend modules imported successfully.")

except ImportError as e:
    print(
        f"FATAL: Could not import modules for backend '{ACTIVE_DB_BACKEND}'. "
        f"Ensure the backend directory and files exist and are correctly named. Details: {e}"
    )
    exit(1)
except AttributeError as e:
    print(
        f"FATAL: A required function (lifespan or tool) might be missing in the '{ACTIVE_DB_BACKEND}' backend modules. Details: {e}"
    )
    exit(1)


# --- Create FastMCP Application ---
mcp_app = FastMCP(
    title=f"{ACTIVE_DB_BACKEND.capitalize()} MCP Service",
    description=f"MCP Server for interacting with a {ACTIVE_DB_BACKEND} database.",
    version="1.0.0",
    lifespan=app_lifespan,  # Assign the dynamically loaded lifespan
    host=os.environ.get("MCP_HOST", "0.0.0.0"),
    port=int(os.environ.get("MCP_PORT", 8888)),
)


# --- Register Tools ---
# Helper function to register if tool exists
def register_tool_if_exists(tool_func, tool_name):
    if tool_func:
        mcp_app.add_tool(tool_func)
        print(f"INFO: Tool '{tool_name}' registered.")
    else:
        print(
            f"WARN: Tool '{tool_name}' not found in {ACTIVE_DB_BACKEND} backend, not registered."
        )


print("INFO: Registering tools...")
if ACTIVE_DB_BACKEND == "sqlite":
    register_tool_if_exists(tool_get_schema, "get_database_schema")
    register_tool_if_exists(tool_execute_query, "execute_query")
elif ACTIVE_DB_BACKEND == "postgres":
    register_tool_if_exists(tool_list_available_databases, "list_available_databases")
    register_tool_if_exists(tool_list_database_objects, "list_database_objects")
    # ... register tools อื่นๆ ของ postgres ...
    register_tool_if_exists(tool_search_data, "search_data")
    register_tool_if_exists(tool_execute_raw_sql, "execute_raw_sql")

print("INFO: Tool registration complete.")


# --- Run the Application ---
if __name__ == "__main__":
    # Check if the lifespan context successfully created a DB pool
    # This is a simplified check; robust checks should be in the lifespan itself
    # or tools should gracefully handle a None db_pool.
    # Note: Accessing lifespan_context directly here before app runs isn't standard.
    # The check for db_pool availability should primarily be within tools.

    # Determine transport and port (example for HTTP)
    # transport_type = os.environ.get("MCP_TRANSPORT", "stdio") # Default to stdio
    # app_port = int(os.environ.get("APP_PORT", 8000))

    print(f"Starting MCP server (Backend: {ACTIVE_DB_BACKEND})...")
    # if transport_type.lower() == "http":
    #     print(f"INFO: Running with HTTP transport on port {app_port}")
    #     mcp_app.run(transport="http", port=app_port)
    # else:
    #     print("INFO: Running with STDIO transport")
    mcp_app.run(
        transport="sse",
    )
