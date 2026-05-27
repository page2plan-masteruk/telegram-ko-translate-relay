import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient


BASE_DIR = Path(__file__).resolve().parent


def env_required(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is missing in .env")
    return value


async def main():
    load_dotenv()

    api_id = int(env_required("TELEGRAM_API_ID"))
    api_hash = env_required("TELEGRAM_API_HASH")

    client = TelegramClient(str(BASE_DIR / "telegram_session"), api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        raise SystemExit("Telegram session is not authorized. Run login_telegram.py first.")

    print("Accessible Telegram channels/groups:")
    async for dialog in client.iter_dialogs():
        if not (dialog.is_channel or dialog.is_group):
            continue

        entity = dialog.entity
        username = getattr(entity, "username", None)
        title = getattr(entity, "title", None) or dialog.name
        print(f"- title={title!r} username={username!r} id={entity.id}")


if __name__ == "__main__":
    asyncio.run(main())
