import asyncio
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

from main import (
    build_message,
    download_message_image,
    env_required,
    image_url_for_kakao,
    resolve_channel,
    send_kakao_image_message,
    send_kakao_message,
    translate_full_text,
)


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
    async for message in client.iter_messages(entity, limit=100):
        if not message.photo:
            continue

        original = (message.text or "").strip()
        translated = translate_full_text(original) if original else "텍스트 없이 이미지가 포함된 메시지입니다."
        image_path = await download_message_image(client, message)
        image_url = image_url_for_kakao(Path(image_path)) if image_path else None

        if image_url:
            send_kakao_image_message("[TEST] Telegram 이미지", translated, image_url)
            if original:
                send_kakao_message("[TEST]\n" + build_message(original, translated))
        else:
            text = "[TEST]\n"
            if original:
                text += build_message(original, translated)
            else:
                text += "[Telegram 이미지]\n\n텍스트 없이 이미지가 포함된 메시지입니다."
            text += f"\n\n[이미지 저장 위치]\n{image_path}"
            send_kakao_message(text)

        print(f"Image pipeline test succeeded with Telegram message #{message.id}.")
        print(f"Downloaded image: {image_path}")
        if image_url:
            print(f"Kakao image URL: {image_url}")
        return

    raise SystemExit("No recent Telegram photo messages found for image testing.")


if __name__ == "__main__":
    asyncio.run(main())
