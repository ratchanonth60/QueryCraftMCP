import sqlite3
from typing import Any, Dict

from mcp.server.fastmcp import Context  # For type hinting ctx

from .lifespan import SQLiteAppContext  # For type hinting


# Tool get_schema (ปรับจาก resource เดิมของคุณ)
# @mcp.tool() # การ register จะทำใน main.py
def get_database_schema(ctx: Context) -> Dict[str, Any]:
    """Provides the database schema for all tables."""
    lifespan_ctx = ctx.request_context.lifespan_context
    if not isinstance(lifespan_ctx, SQLiteAppContext):
        return {"error": "SQLite context not available."}

    db_path = lifespan_ctx.db_path

    try:
        conn = sqlite3.connect(db_path)
        # ดึง schema ของทุกตาราง
        cursor = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        schema_rows = cursor.fetchall()
        conn.close()

        if not schema_rows:
            return {"schema": "No tables found in the database."}

        # รวม schema statements ทั้งหมด
        full_schema = "\n\n".join(row[0] for row in schema_rows if row[0])
        return {"schema": full_schema}
    except Exception as e:
        print(f"Error in get_database_schema (SQLite): {e}")
        return {"error": f"An error occurred: {type(e).__name__}"}
