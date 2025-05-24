import sqlite3
from typing import Any, Dict, List, Optional  # เพิ่ม List, Optional

from mcp.server.fastmcp import Context

from .lifespan import SQLiteAppContext


# @mcp.tool() # การ register จะทำใน main.py
def execute_query(
    ctx: Context, sql_query: str, params: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """
    Executes a given SQL query against the SQLite database.
    [!] SECURITY WARNING: Directly executing SQL from LLM can be risky.
    Consider sanitization or using this tool only with trusted queries.
    """
    lifespan_ctx = ctx.request_context.lifespan_context
    if not isinstance(lifespan_ctx, SQLiteAppContext):
        return {"error": "SQLite context not available."}

    db_path = lifespan_ctx.db_path

    # คำเตือน: การรัน SQL ดิบๆ จาก LLM มีความเสี่ยงสูงมาก
    # ควรมีมาตรการป้องกัน SQL Injection ที่เข้มงวด หรือใช้ Tool นี้กับ Query ที่เชื่อถือได้เท่านั้น
    # ตัวอย่างนี้ยังไม่มีการป้องกันที่เพียงพอสำหรับ Production ที่รับ Input จาก LLM โดยตรง
    print(f"SQLite: Executing query: {sql_query} with params: {params}")

    # Basic check (can be easily bypassed, not a real security measure)
    if not sql_query.strip().upper().startswith("SELECT"):
        # For SQLite, other commands like PRAGMA might be useful for schema reading
        # but allowing arbitrary commands is risky.
        # Adjust this check based on your trust model.
        # return {"error": "Only SELECT statements are tentatively permitted."}
        pass  # Allowing more than SELECT for now, but be very careful.

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        if params:
            cursor.execute(sql_query, tuple(params))
        else:
            cursor.execute(sql_query)

        # ดึงชื่อคอลัมน์
        column_names = (
            [description[0] for description in cursor.description]
            if cursor.description
            else []
        )

        result_rows = cursor.fetchall()
        conn.close()

        # แปลงผลลัพธ์เป็น list of dicts เพื่อให้ LLM ใช้งานง่าย
        formatted_results = [dict(zip(column_names, row)) for row in result_rows]

        return {
            "data": formatted_results,
            "columns": column_names,
            "row_count": len(formatted_results),
        }
    except sqlite3.Error as e:  # Catch specific SQLite errors
        print(f"SQLite query error: {e}")
        return {"error": f"SQLite Error: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error during SQLite query: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}"}
