import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

from main import (
    build_message,
    build_translated_only_message,
    env_bool,
    env_required,
    resolve_channel,
    send_kakao_message,
    send_telegram_text,
    translate_full_text,
)


BASE_DIR = Path(__file__).resolve().parent


async def main():
    load_dotenv()

    api_id = int(env_required("TELEGRAM_API_ID"))
    api_hash = env_required("TELEGRAM_API_HASH")
    source = env_required("TELEGRAM_CHANNEL")
    target = env_required("TELEGRAM_TARGET_CHANNEL")
    send_to_kakao = env_bool("SEND_TO_KAKAO", True)
    send_to_telegram = env_bool("SEND_TO_TELEGRAM", True)

    client = TelegramClient(str(BASE_DIR / "telegram_session"), api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        raise SystemExit("Telegram session is not authorized. Run login_telegram.py first.")

    source_entity = await resolve_channel(client, source)
    target_entity = await resolve_channel(client, target)

    async for message in client.iter_messages(source_entity, limit=20):
        if not message.text:
            continue

        original = message.text.strip()
        translated = translate_full_text(original)

        if send_to_kakao:
            send_kakao_message("[TEST DUAL]\n" + build_message(original, translated))

        if send_to_telegram:
            await send_telegram_text(
                client,
                target_entity,
                "[TEST DUAL]\n" + build_translated_only_message(translated),
            )

        print(f"Dual pipeline test succeeded with Telegram message #{message.id}.")
        return

    raise SystemExit("No recent text messages found for dual pipeline testing.")


if __name__ == "__main__":
    asyncio.run(main())
