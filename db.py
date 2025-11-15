# db.py
import aiosqlite
from typing import List, Tuple, Optional, Dict, Any
from configs import DB_FILENAME

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    chat_id INTEGER NOT NULL,
    chat_title TEXT,
    message_text TEXT,
    timestamp TEXT NOT NULL
);
"""
CREATE_IDX_USER_TS = "CREATE INDEX IF NOT EXISTS idx_user_ts ON messages(user_id, timestamp);"
CREATE_IDX_USERNAME_TS = "CREATE INDEX IF NOT EXISTS idx_username_ts ON messages(username, timestamp);"

async def init_db() -> None:
    async with aiosqlite.connect(DB_FILENAME) as db:
        await db.execute(CREATE_SQL)
        await db.execute(CREATE_IDX_USER_TS)
        await db.execute(CREATE_IDX_USERNAME_TS)
        await db.commit()

async def store_message(
    user_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    chat_id: int,
    chat_title: Optional[str],
    message_text: Optional[str],
    timestamp_iso: str
) -> None:
    async with aiosqlite.connect(DB_FILENAME) as db:
        await db.execute(
            """
            INSERT INTO messages (user_id, username, first_name, last_name, chat_id, chat_title, message_text, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, first_name, last_name, chat_id, chat_title, message_text, timestamp_iso)
        )
        await db.commit()

async def query_messages_for_export(
    username_or_id: str,
    allowed_groups: Optional[set] = None,
    chat_id: Optional[int] = None,
    start_ts: Optional[str] = None,
    end_ts: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Returns messages matching username_or_id (either username without @ or numeric user_id).
    Results sorted by timestamp DESC (latest first).
    """
    clauses = []
    params = []

    if username_or_id.isdigit():
        clauses.append("user_id = ?")
        params.append(int(username_or_id))
    else:
        clauses.append("username = ?")
        params.append(username_or_id)

    # restrict to allowed groups if provided
    if allowed_groups:
        placeholders = ",".join("?" for _ in allowed_groups)
        clauses.append(f"chat_id IN ({placeholders})")
        params.extend(sorted(list(allowed_groups)))

    if chat_id is not None:
        clauses.append("chat_id = ?")
        params.append(chat_id)
    if start_ts is not None:
        clauses.append("timestamp >= ?")
        params.append(start_ts)
    if end_ts is not None:
        clauses.append("timestamp <= ?")
        params.append(end_ts)

    where_sql = " AND ".join(clauses) if clauses else "1"
    limit_sql = f"LIMIT {int(limit)}" if limit is not None else ""

    sql = f"""
    SELECT id, user_id, username, first_name, last_name, chat_id, coalesce(chat_title, ''), coalesce(message_text, ''), timestamp
    FROM messages
    WHERE {where_sql}
    ORDER BY timestamp DESC
    {limit_sql}
    """

    rows = []
    async with aiosqlite.connect(DB_FILENAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, params) as cur:
            fetched = await cur.fetchall()
            for r in fetched:
                rows.append({
                    "id": r[0],
                    "user_id": r[1],
                    "username": r[2],
                    "first_name": r[3],
                    "last_name": r[4],
                    "chat_id": r[5],
                    "chat_title": r[6],
                    "message_text": r[7],
                    "timestamp": r[8],
                })
    return rows