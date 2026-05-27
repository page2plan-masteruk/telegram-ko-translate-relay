import asyncio
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

from main import build_message, env_required, resolve_channel, send_kakao_message, translate_full_text


BASE_DIR = Path(__file__).resolve().parent


async def main():
    load_dotenv()

    api_id = int(env_required("TELEGRAM_API_ID"))
    api_hash = env_required("TELEGRAM_API_HASH")
    channel = env_required("TELEGRAM_CHANNEL")

    client = TelegramClient(str(BASE_DIR / "telegram_session"), api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        raise SystemExit("Telegram session is not authorized. Run login_telegram.py first.")

    entity = await resolve_channel(client, channel)
    async for message in client.iter_messages(entity, limit=20):
        if not message.text:
            continue

        original = message.text.strip()
        translated = translate_full_text(original)
        kakao_text = "[TEST]\n" + build_message(original, translated)
        send_kakao_message(kakao_text)
        print(f"End-to-end test succeeded with Telegram message #{message.id}.")
        return

    raise SystemExit("No recent text messages found for end-to-end testing.")


if __name__ == "__main__":
    asyncio.run(main())
