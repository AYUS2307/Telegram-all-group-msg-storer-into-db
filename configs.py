# config.py
BOT_TOKEN = "8466407032:AAEkz0oZg956uRpPBOn0KoQ9PTX5yCKoflI"

# Allowed group chat IDs
ALLOWED_GROUP_IDS = {
    -1002036072316,
    -1002276727546,
    -1001942377118,
    -1001671357572,
    -1002027891366,
    -1001861957646
}

# Admin user IDs allowed to run retrieval / export commands
ADMIN_IDS = {
    6006815002
}

# Database filename
DB_FILENAME = "messages.db"

# Max rows returned by default (set None for no limit)
DEFAULT_LIMIT = 1000