
# Telegram Message Logger (aiogram)

A Telegram bot that records messages from specified groups into an async SQLite database and lets admins export a user’s messages as a downloadable JSON file (newest-first). Built with aiogram + aiosqlite for non-blocking DB I/O.

### Features
- Listens to a fixed set of allowed groups and stores every user message (text and captions) into SQLite.  
- Fields stored: id, user_id, username, first_name, last_name, chat_id, chat_title, message_text, timestamp.  
- Admin-only export command that returns a downloadable JSON file containing messages for a user across allowed groups, sorted newest-first.  
- Optional filters: chat_id, start_iso, end_iso, limit.  
- Uses temporary files and sends the JSON file to the admin’s private chat with the bot.  
- Safe defaults: query limits and admin-only access.

---

## Requirements
- Python 3.10+  
- Dependencies (listed in requirements.txt):  
  - aiogram (v3 beta series)  
  - aiosqlite  
  - ujson (fast JSON writing)

Example requirements.txt:
```
aiogram>=3.0.0b7
aiosqlite>=0.17.0
ujson>=5.8.0
```

---

## Installation

1. Clone the repo or copy project files into a folder (see structure below).  
2. Create and activate a virtual environment:
   - Unix/macOS: `python -m venv venv && source venv/bin/activate`
   - Windows: `python -m venv venv && venv\Scripts\activate`
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Edit `config.py` with your bot token, allowed group IDs, admin IDs, and DB filename.

Project structure:
```
telegram_message_logger/
├── README.md
├── requirements.txt
├── config.py
├── db.py
└── bot.py
```

---

## Configuration (config.py)
Set the following values:

- BOT_TOKEN: your bot token from BotFather.  
- ALLOWED_GROUP_IDS: set of group chat IDs the bot should monitor.  
- ADMIN_IDS: set of Telegram user IDs permitted to run export commands.  
- DB_FILENAME: path to SQLite file (default: messages.db).  
- DEFAULT_LIMIT: default row limit for exports (recommended non-zero).  

Example snippet:
```python
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
ALLOWED_GROUP_IDS = { -1001234567890, -1001122334455 }
ADMIN_IDS = { 123456789 }
DB_FILENAME = "messages.db"
DEFAULT_LIMIT = 1000
```

Important: admins must have started the bot (pressed /start) at least once so the bot can DM them.

---

## Run
1. Initialize DB and start the bot:
   - `python bot.py`
   - On startup the bot ensures the DB schema and indexes exist.

The bot runs in long-polling mode by default. For production consider a process manager (systemd, docker, supervisor).

---

## Exporting and Searchinng msgs Commands & Usage 

All admin commands are restricted to IDs in `config.ADMIN_IDS`.

- /export_messages <username_or_userid> [chat_id] [start_iso] [end_iso] [limit]  
  - Exports messages for a username (without @) or numeric user_id.  
  - Optional positional args:
    - chat_id: restrict to a single group (use group chat ID like -1001234567890) or `-` to skip.
    - start_iso / end_iso: ISO timestamps (e.g., 2024-01-01T00:00:00) or `-` to skip.
    - limit: number of messages to return (integer), or `-` to use DEFAULT_LIMIT.
  - Behavior:
    - The bot queries messages across configured allowed groups (unless chat_id is provided).
    - Results are sorted by timestamp DESC (newest first).
    - The bot writes results to a temporary JSON file and sends it as a downloadable document to the admin’s private chat with the bot.
    - If command invoked in a group, the bot notifies the invoking chat that it will send the file to admin DM.

Examples:
- Basic export (default limit):  
  `/export_messages @alice`
- Export across a single group and date range:  
  `/export_messages 123456789 -1001122334455 2024-01-01T00:00:00 2024-01-31T23:59:59 500`
- Use `-` to skip optional params:  
  `/export_messages @alice - - 2024-12-31T23:59:59 100`

Notes:
- If the admin hasn’t started a DM with the bot, Telegram will prevent the bot from sending a private document — ensure admins have previously started the bot.
- The JSON file contains an array of message objects with keys: id, user_id, username, first_name, last_name, chat_id, chat_title, message_text, timestamp.

---

## Security, limits, and best practices
- Only IDs in ADMIN_IDS can export data. Keep that list minimal.  
- DEFAULT_LIMIT is a safety guard against huge exports; set it to a sensible number (e.g., 1000).  
- For very large exports, consider adding inline confirmation or pagination to avoid accidental heavy jobs.  
- If you require media file contents or file downloads, extend schema to store file_id and file_type, and implement secure retrieval with rate limits.  
- Run the bot under a process manager and monitor DB size; rotate or archive old data if needed.

---

## Extensibility ideas (next steps)
- Add inline confirmation before large exports (show estimated row count / size).  
- Implement cursor-based pagination and inline keyboard navigation to preview data.  
- Export CSV option or stream JSON in chunks.  
- Store media metadata (file_id, mime type) and optionally download attachments.  
- Move to server-backed DB (Postgres) if write volume increases.

---

