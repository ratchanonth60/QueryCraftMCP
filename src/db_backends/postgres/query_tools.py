from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context

from ..postgres.lifespan import PostgresAppContext


async def search_data(
    ctx: Context,
    table_name: str,
    search_term: Optional[str] = None,
    search_fields: Optional[List[str]] = None,
    filters: Optional[
        List[Dict[str, Any]]
    ] = None,  # Example: [{"field": "price", "op": ">", "value": 100}]
    sort_by: Optional[
        Dict[str, str]
    ] = None,  # Example: {"field": "name", "direction": "asc"}
    limit: int = 10,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Searches data in the specified table.
    (Simplified: add proper filter and sort construction based on your needs)
    """
    lifespan_ctx = ctx.request_context.lifespan_context
    if not isinstance(lifespan_ctx, PostgresAppContext) or not lifespan_ctx.db_pool:
        return {"error": "PostgreSQL connection pool not available."}
    db_pool = lifespan_ctx.db_pool

    if not table_name.isalnum():  # Basic sanitization
        return {"error": "Invalid table name."}

    query_params = []
    where_clauses = []
    param_idx = 1

    if search_term and search_fields:
        clauses = []
        for field in search_fields:
            if not field.isalnum():
                continue  # Basic sanitization
            clauses.append(f"{field} ILIKE ${param_idx}")
            query_params.append(f"%{search_term}%")
            param_idx += 1
        if clauses:
            where_clauses.append(f"({' OR '.join(clauses)})")

    # Add more complex filter construction here based on 'filters' input
    # Example for a simple filter:
    if filters:
        for f in filters:
            # Validate f["field"], f["op"]
            where_clauses.append(f"{f['field']} {f['op']} ${param_idx}")
            query_params.append(f["value"])
            param_idx += 1

    sql = f"SELECT * FROM {table_name}"  # Table name from a whitelist or further sanitized
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    # Add sorting
    if sort_by:
        sql += f" ORDER BY {sort_by['field']} {sort_by.get('direction', 'asc').upper()}"

    sql += f" LIMIT ${param_idx} OFFSET ${param_idx + 1}"
    query_params.extend([limit, offset])

    try:
        async with db_pool.acquire() as conn:
            # print(f"Executing: {sql} with {query_params}") # For debugging
            rows = await conn.fetch(sql, *query_params)
        return {"data": [dict(row) for row in rows]}
    except Exception as e:
        print(f"Error in search_data: {e}")
        return {"error": f"Database query failed: {type(e).__name__}"}


async def execute_raw_sql(
    ctx: Context, query: str, params: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """
    [!] SECURITY WARNING [!] Executes a raw SQL query.
    Highly discouraged for LLM-generated queries due to SQL injection risks.
    Use with extreme caution and only with trusted, validated queries and a read-only DB user.
    Only SELECT statements are tentatively permitted by a basic check.
    """
    lifespan_ctx = ctx.request_context.lifespan_context
    if not isinstance(lifespan_ctx, PostgresAppContext) or not lifespan_ctx.db_pool:
        return {"error": "PostgreSQL connection pool not available."}
    db_pool = lifespan_ctx.db_pool

    # Basic check to allow only SELECT (very rudimentary, can be bypassed)
    if not query.strip().upper().startswith("SELECT"):
        return {
            "error": "Only SELECT statements are tentatively permitted for raw execution."
        }

    # Add more disallowed keywords if necessary, but this is not foolproof
    disallowed_keywords = [
        "DROP",
        "DELETE",
        "INSERT",
        "UPDATE",
        "TRUNCATE",
        "ALTER",
        "CREATE",
        "EXECUTE",
    ]
    query_upper = query.upper()
    for keyword in disallowed_keywords:
        if keyword in query_upper:
            return {
                "error": f"Query contains disallowed keyword '{keyword}'. Raw execution denied."
            }

    try:
        async with db_pool.acquire() as conn:
            print(f"Executing RAW SQL (with caution): {query}, params: {params}")
            if params:
                rows = await conn.fetch(query, *params)
            else:
                rows = await conn.fetch(query)

        # For non-SELECT commands that don't return rows but are somehow allowed (e.g. EXPLAIN)
        # conn.execute might be used, and it returns a status string.
        # For SELECT, fetch returns a list of Record objects.
        return {"data": [dict(row) for row in rows]}
    except Exception as e:
        print(f"Error in execute_raw_sql: {e}")
        return {"error": f"Raw SQL execution failed: {type(e).__name__}"}
