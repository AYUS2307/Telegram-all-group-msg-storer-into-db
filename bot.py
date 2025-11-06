# bot.py
import asyncio
import html
import tempfile
import os
import ujson as json
from datetime import timezone
from typing import Optional

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

import db
import configs

bot = Bot(token=db.BOT_TOKEN)
dp = Dispatcher()

def utc_iso_from_message_date(msg_date) -> str:
    return msg_date.astimezone(timezone.utc).isoformat()

@dp.message(lambda message: message.chat.id in db.ALLOWED_GROUP_IDS, content_types=types.ContentType.ANY)
async def handle_group_message(message: Message) -> None:
    user = message.from_user
    chat = message.chat
    if not user:
        return

    text = message.text or message.caption or ""  # store text or caption
    ts = utc_iso_from_message_date(message.date) if message.date else None
    # store message record
    await configs.store_message(
        user_id=user.id,
        username=(user.username or None),
        first_name=(user.first_name or None),
        last_name=(user.last_name or None),
        chat_id=chat.id,
        chat_title=(chat.title or None),
        message_text=text,
        timestamp_iso=ts
    )

@dp.message(Command(commands=["export_messages"]))
async def export_messages_cmd(message: Message) -> None:
    """
    /export_messages <username_or_userid> [chat_id] [start_iso] [end_iso] [limit]
    Outputs a downloadable JSON file (sent to admin's DM with the bot).
    """
    from_user = message.from_user
    if not from_user or from_user.id not in db.ADMIN_IDS:
        await message.reply("Unauthorized. This command is for admins only.")
        return

    args = (message.get_args() or "").split()
    if not args:
        await message.reply("Usage: /export_messages <username_or_userid> [chat_id] [start_iso] [end_iso] [limit]")
        return

    key = args[0].lstrip("@")
    chat_id = None
    start_ts = None
    end_ts = None
    limit = db.DEFAULT_LIMIT

    try:
        if len(args) >= 2 and args[1] != "-":
            chat_id = int(args[1])
        if len(args) >= 3 and args[2] != "-":
            start_ts = args[2]
        if len(args) >= 4 and args[3] != "-":
            end_ts = args[3]
        if len(args) >= 5 and args[4] != "-":
            limit = int(args[4])
    except Exception:
        await message.reply("Error parsing arguments. Ensure chat_id and limit are integers; timestamps are ISO strings. Use '-' to skip optional values.")
        return

    # Query DB for messages across allowed groups
    rows = await configs.query_messages_for_export(
        username_or_id=key,
        allowed_groups=db.ALLOWED_GROUP_IDS,
        chat_id=chat_id,
        start_ts=start_ts,
        end_ts=end_ts,
        limit=limit
    )

    if not rows:
        await message.reply("No messages found for that user with the given filters.")
        return

    # Create JSON content: list of message dicts (already ordered DESC)
    json_content = json.dumps(rows, ensure_ascii=False, indent=2)

    # write to temporary file
    tmp_dir = tempfile.gettempdir()
    filename = f"messages_{key}.json"
    tmp_path = os.path.join(tmp_dir, filename)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(json_content)

    try:
        # send file to admin's private chat (use admin id)
        admin_chat_id = from_user.id
        # send as document (downloadable)
        doc = FSInputFile(tmp_path)
        # send a short message first in the invoking chat to notify admin (optional)
        if message.chat.type != "private":
            await message.reply("I will send the exported JSON file to your private chat with me.")
        # send the file in private chat (bot can send to admin.id even if invoked in group)
        await bot.send_document(admin_chat_id, doc, caption=f"Messages export for {key} (sorted newest first).")
    except Exception as e:
        # If sending fails (e.g., bot blocked), notify in the invoking chat
        await message.reply(f"Failed to send file to admin's DM: {e}")
    finally:
        # cleanup temporary file
        try:
            os.remove(tmp_path)
        except Exception:
            pass

async def on_startup():
    await configs.init_db()

if __name__ == "__main__":
    try:
        asyncio.run(on_startup())
        from aiogram import executor
        executor.start_polling(dp, skip_updates=True)
    finally:
        asyncio.run(bot.session.close())