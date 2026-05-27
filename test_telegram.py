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


async def resolve_channel(client, channel):
    try:
        return await client.get_entity(channel)
    except ValueError as original_error:
        candidates = {channel.strip()}
        if channel.startswith("@"):
            candidates.add(channel[1:].strip())

        async for dialog in client.iter_dialogs():
            names = {
                str(getattr(dialog, "name", "")).strip(),
                str(getattr(dialog.entity, "title", "")).strip(),
                str(getattr(dialog.entity, "username", "")).strip(),
                str(getattr(dialog.entity, "id", "")).strip(),
            }
            if candidates & names:
                return dialog.entity

        raise RuntimeError(
            "Could not find TELEGRAM_CHANNEL. Use a public @username, t.me link, "
            "numeric channel ID, or the exact chat title visible in Telegram."
        ) from original_error


async def main():
    load_dotenv()

    api_id = int(env_required("TELEGRAM_API_ID"))
    api_hash = env_required("TELEGRAM_API_HASH")
    phone = env_required("TELEGRAM_PHONE")
    channel = env_required("TELEGRAM_CHANNEL")

    client = TelegramClient(str(BASE_DIR / "telegram_session"), api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        print("Telegram session is not authorized yet.")
        print("Do not retry repeatedly if Telegram is rate-limiting code requests.")
        print("When the limit is cleared, run: python login_telegram.py")
        return

    entity = await resolve_channel(client, channel)
    print(f"Connected to: {getattr(entity, 'title', channel)}")
    print("Recent text messages:")

    count = 0
    async for message in client.iter_messages(entity, limit=10):
        if not message.text:
            continue
        preview = " ".join(message.text.strip().split())
        print(f"- #{message.id}: {preview[:160]}")
        count += 1
        if count >= 3:
            break

    if count == 0:
        print("No recent text messages were found.")


if __name__ == "__main__":
    asyncio.run(main())
