import asyncio
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

from main import (
    download_message_image,
    env_required,
    resolve_channel,
    send_telegram_result,
    translate_full_text,
)


BASE_DIR = Path(__file__).resolve().parent


async def main():
    load_dotenv()

    api_id = int(env_required("TELEGRAM_API_ID"))
    api_hash = env_required("TELEGRAM_API_HASH")
    source = env_required("TELEGRAM_CHANNEL")
    target = env_required("TELEGRAM_TARGET_CHANNEL")

    client = TelegramClient(str(BASE_DIR / "telegram_session"), api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        raise SystemExit("Telegram session is not authorized. Run login_telegram.py first.")

    source_entity = await resolve_channel(client, source)
    target_entity = await resolve_channel(client, target)

    async for message in client.iter_messages(source_entity, limit=100):
        if not message.photo:
            continue

        original = (message.text or "").strip()
        translated = translate_full_text(original) if original else "텍스트 없이 이미지가 포함된 메시지입니다."
        image_path = await download_message_image(client, message)
        await send_telegram_result(
            client,
            target_entity,
            "[TEST IMAGE]\n" + translated,
            image_path=image_path,
        )

        print(f"Telegram image target test succeeded with Telegram message #{message.id}.")
        print(f"Downloaded image: {image_path}")
        return

    raise SystemExit("No recent Telegram photo messages found for Telegram image target testing.")


if __name__ == "__main__":
    asyncio.run(main())
