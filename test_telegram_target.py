import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

from main import env_required, resolve_channel


BASE_DIR = Path(__file__).resolve().parent


async def main():
    load_dotenv()

    api_id = int(env_required("TELEGRAM_API_ID"))
    api_hash = env_required("TELEGRAM_API_HASH")
    target = env_required("TELEGRAM_TARGET_CHANNEL")

    client = TelegramClient(str(BASE_DIR / "telegram_session"), api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        raise SystemExit("Telegram session is not authorized. Run login_telegram.py first.")

    entity = await resolve_channel(client, target)
    title = getattr(entity, "title", None) or getattr(entity, "username", None) or str(entity.id)
    await client.send_message(entity, "[TEST] Telegram 번역방 연결 테스트입니다.")
    print(f"Telegram target test succeeded: {title}")


if __name__ == "__main__":
    asyncio.run(main())
