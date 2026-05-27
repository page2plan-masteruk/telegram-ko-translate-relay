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
    phone = env_required("TELEGRAM_PHONE")

    print("This will request a Telegram login code if the saved session is not authorized.")
    print("If you recently saw SendCodeUnavailableError, stop now and wait before retrying.")

    client = TelegramClient(str(BASE_DIR / "telegram_session"), api_id, api_hash)
    await client.start(phone=phone)

    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"Telegram login succeeded: {getattr(me, 'username', None) or me.id}")
    else:
        print("Telegram login did not complete.")


if __name__ == "__main__":
    asyncio.run(main())
