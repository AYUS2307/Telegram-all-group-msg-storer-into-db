# bot.py
import asyncio
import os
import tempfile
import ujson as json
from datetime import timezone

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, FSInputFile

import db
import configs

bot = Bot(token=configs.BOT_TOKEN)
dp = Dispatcher()

def utc_iso_from_message_date(msg_date) -> str:
    return msg_date.astimezone(timezone.utc).isoformat()

# --- Group Message Handler ---
# FIX: Use configs.ALLOWED_GROUP_IDS, not db.ALLOWED_GROUP_IDS
@dp.message(lambda message: message.chat.id in configs.ALLOWED_GROUP_IDS)
async def handle_group_message(message: Message) -> None:
    user = message.from_user
    chat = message.chat
    if not user:
        return

    text = message.text or message.caption or ""
    ts = utc_iso_from_message_date(message.date) if message.date else None
    
    # FIX: Call db.store_message, not configs.store_message
    await db.store_message(
        user_id=user.id,
        username=(user.username or None),
        first_name=(user.first_name or None),
        last_name=(user.last_name or None),
        chat_id=chat.id,
        chat_title=(chat.title or None),
        message_text=text,
        timestamp_iso=ts
    )

# --- Export Command Handler ---
@dp.message(Command(commands=["export_messages"]))
async def export_messages_cmd(message: Message, command: CommandObject) -> None:
    """
    Usage: /export_messages <username_or_userid> [chat_id] [start_iso] [end_iso] [limit]
    """
    from_user = message.from_user
    
    # FIX: Use configs.ADMIN_IDS, not db.ADMIN_IDS
    if not from_user or from_user.id not in configs.ADMIN_IDS:
        await message.reply("Unauthorized. This command is for admins only.")
        return

    # FIX: Use command.args for arguments in Aiogram 3
    args_str = command.args or ""
    args = args_str.split()

    if not args:
        await message.reply("Usage: /export_messages <username_or_userid> [chat_id] [start_iso] [end_iso] [limit]")
        return

    key = args[0].lstrip("@")
    chat_id = None
    start_ts = None
    end_ts = None
    limit = configs.DEFAULT_LIMIT

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

    # Query DB
    rows = await db.query_messages_for_export(
        username_or_id=key,
        allowed_groups=configs.ALLOWED_GROUP_IDS,
        chat_id=chat_id,
        start_ts=start_ts,
        end_ts=end_ts,
        limit=limit
    )

    if not rows:
        await message.reply("No messages found for that user with the given filters.")
        return

    # Create JSON content
    json_content = json.dumps(rows, ensure_ascii=False, indent=2)

    tmp_dir = tempfile.gettempdir()
    filename = f"messages_{key}.json"
    tmp_path = os.path.join(tmp_dir, filename)
    
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(json_content)

    try:
        admin_chat_id = from_user.id
        doc = FSInputFile(tmp_path)
        
        if message.chat.type != "private":
            await message.reply("I will send the exported JSON file to your private chat.")
            
        await bot.send_document(admin_chat_id, doc, caption=f"Messages export for {key} (sorted newest first).")
    except Exception as e:
        await message.reply(f"Failed to send file to admin's DM: {e}")
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

async def main():
    await db.init_db()
    # FIX: Use dp.start_polling for Aiogram 3
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())