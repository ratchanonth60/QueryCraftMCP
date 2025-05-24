from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context

from ..postgres.lifespan import PostgresAppContext


async def list_available_databases(ctx: Context) -> Dict[str, Any]:
    """Lists available databases the connected user can see."""
    lifespan_ctx = ctx.request_context.lifespan_context
    if not isinstance(lifespan_ctx, PostgresAppContext) or not lifespan_ctx.db_pool:
        return {"error": "PostgreSQL connection pool not available."}

    db_pool = lifespan_ctx.db_pool
    query = """
        SELECT datname FROM pg_database
        WHERE datistemplate = false AND has_database_privilege(datname, 'CONNECT')
        ORDER BY datname;
    """
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query)
        database_names = [row["datname"] for row in rows]
        return {"databases": database_names, "count": len(database_names)}
    except Exception as e:
        print(f"Error in list_available_databases: {e}")
        return {"error": f"An error occurred: {type(e).__name__}"}


async def list_database_objects(
    ctx: Context, schema_name: str = "public", object_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Lists tables and views within a specified database schema."""
    lifespan_ctx = ctx.request_context.lifespan_context
    if not isinstance(lifespan_ctx, PostgresAppContext) or not lifespan_ctx.db_pool:
        return {"error": "PostgreSQL connection pool not available."}
    db_pool = lifespan_ctx.db_pool

    if object_types is None:
        object_types = ["BASE TABLE", "VIEW"]

    # Basic validation for object_types
    valid_object_types = ["BASE TABLE", "VIEW"]
    for obj_type in object_types:
        if obj_type.upper() not in valid_object_types:
            return {
                "error": f"Invalid object_type '{obj_type}'. Valid types are: {valid_object_types}."
            }

    query = """
        SELECT table_name, table_schema, table_type
        FROM information_schema.tables
        WHERE table_schema = $1 AND table_type = ANY($2)
        ORDER BY table_schema, table_type, table_name;
    """
    try:
        async with db_pool.acquire() as conn:
            # Note: asyncpg expects a list for ANY($array_parameter)
            rows = await conn.fetch(query, schema_name, object_types)
        db_objects = [
            {
                "name": r["table_name"],
                "schema": r["table_schema"],
                "type": r["table_type"],
            }
            for r in rows
        ]
        return {"objects": db_objects}
    except Exception as e:
        print(f"Error in list_database_objects: {e}")
        return {"error": f"An error occurred: {type(e).__name__}"}


async def get_object_columns(
    ctx: Context, object_name: str, schema_name: str = "public"
) -> Dict[str, Any]:
    """Retrieves column information for a specified table or view."""
    lifespan_ctx = ctx.request_context.lifespan_context
    if not isinstance(lifespan_ctx, PostgresAppContext) or not lifespan_ctx.db_pool:
        return {"error": "PostgreSQL connection pool not available."}
    db_pool = lifespan_ctx.db_pool

    query = """
        SELECT column_name, data_type, is_nullable, column_default,
               character_maximum_length, numeric_precision, numeric_scale
        FROM information_schema.columns
        WHERE table_schema = $1 AND table_name = $2
        ORDER BY ordinal_position;
    """
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, schema_name, object_name)
        if not rows:
            return {
                "error": f"Object '{schema_name}.{object_name}' not found or has no columns."
            }

        columns_info = []
        for r in rows:
            col = {
                "name": r["column_name"],
                "data_type": r["data_type"],
                "is_nullable": r["is_nullable"].upper() == "YES",
                "default": r["column_default"],
            }
            if r["character_maximum_length"] is not None:
                col["char_max_len"] = r["character_maximum_length"]
            if r["numeric_precision"] is not None:
                col["num_precision"] = r["numeric_precision"]
            if r["numeric_scale"] is not None:
                col["num_scale"] = r["numeric_scale"]
            columns_info.append(col)
        return {"columns": columns_info}
    except Exception as e:
        print(f"Error in get_object_columns: {e}")
        return {"error": f"An error occurred: {type(e).__name__}"}
