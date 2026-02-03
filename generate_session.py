# Save as generate_session.py, then run: python generate_session.py
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = 38148724   # Your API ID from my.telegram.org
API_HASH = "dba314bf71cef51ab4b9922c18b95cd8"  # Your API Hash

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("Session string (copy this to .env):")
    print(client.session.save())