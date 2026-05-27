import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.channels import CreateChannelRequest

from main import env_required, resolve_channel


BASE_DIR = Path(__file__).resolve().parent


async def main():
    load_dotenv()

    api_id = int(env_required("TELEGRAM_API_ID"))
    api_hash = env_required("TELEGRAM_API_HASH")
    target = os.getenv("TELEGRAM_TARGET_CHANNEL", "").strip()
    title = target[1:].strip() if target.startswith("@") else target
    if not title:
        title = "Korean Translation Feed"

    client = TelegramClient(str(BASE_DIR / "telegram_session"), api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        raise SystemExit("Telegram session is not authorized. Run login_telegram.py first.")

    try:
        entity = await resolve_channel(client, target)
        found_title = getattr(entity, "title", None) or getattr(entity, "username", None) or str(entity.id)
        print(f"Target already exists: {found_title}")
        print(f"TELEGRAM_TARGET_CHANNEL={entity.id}")
        return
    except Exception:
        pass

    result = await client(
        CreateChannelRequest(
            title=title,
            about="Telegram English to Korean translated feed",
            megagroup=False,
        )
    )
    entity = result.chats[0]
    await client.send_message(entity, "[TEST] Telegram 한글 번역방이 생성되었습니다.")

    print(f"Created Telegram target channel: {entity.title}")
    print(f"TELEGRAM_TARGET_CHANNEL={entity.id}")


if __name__ == "__main__":
    asyncio.run(main())
