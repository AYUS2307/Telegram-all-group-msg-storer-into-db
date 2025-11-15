# configs.py
# PASTE YOUR TOKEN HERE
BOT_TOKEN = "paste_your_bot_token_here"

# Allowed group chat IDs (Integers)
ALLOWED_GROUP_IDS = {
    -1001234567890,
    -1009876543210,
    -1001122334455,
    -1005566778899,
    -1009988776655
}

# Admin user IDs allowed to run retrieval / export commands
ADMIN_IDS = {
    123456789
}

# Database filename
DB_FILENAME = "messages.db"

# Max rows returned by default (set None for no limit)
DEFAULT_LIMIT = 1000