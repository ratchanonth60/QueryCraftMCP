import os
import sqlite3
from collections.abc import AsyncIterator
from contextlib import (
    asynccontextmanager,
)
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP  # For type hinting server if needed


@dataclass
class SQLiteAppContext:
    db_path: str
    conn: sqlite3.Connection | None = None


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[SQLiteAppContext]:
    """Manages the SQLite database path for the application lifecycle."""
    db_file_path = os.environ.get(
        "SQLITE_DATABASE_PATH", "database.db"
    )  # Default to database.db

    # ตรวจสอบว่าไฟล์ database (หรือ directory) สามารถเข้าถึงได้ (optional)
    # db_dir = os.path.dirname(os.path.abspath(db_file_path))
    # if not os.path.exists(db_dir):
    #     os.makedirs(db_dir, exist_ok=True)
    #     print(f"SQLite Lifespan: Created directory {db_dir}")

    print(f"SQLite Lifespan: Using database file at '{db_file_path}'")

    # สำหรับ SQLite ที่เป็น file-based อาจจะไม่ต้องทำ "connect/disconnect" ใน lifespan
    # แต่ lifespan ยังมีประโยชน์ในการ set up AppContext ด้วย db_path
    # ถ้าต้องการเปิด connection ค้างไว้ ก็ทำได้ที่นี่
    # conn = None
    try:
        # conn = sqlite3.connect(db_file_path)
        # print(f"SQLite Lifespan: Connection to '{db_file_path}' established.")
        yield SQLiteAppContext(db_path=db_file_path)  # , conn=conn)
    except Exception as e:
        print(f"SQLite Lifespan: Error during setup - {e}")
        # yield SQLiteAppContext(db_path=db_file_path, conn=None) # หรือจัดการ error ตามความเหมาะสม
        raise
    # finally:
    # if conn:
    #     print(f"SQLite Lifespan: Closing connection to '{db_file_path}'.")
    #     conn.close()
