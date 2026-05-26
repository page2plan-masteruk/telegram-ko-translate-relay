import asyncio
import json
import mimetypes
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image, ImageOps
from telethon import TelegramClient


BASE_DIR = Path(__file__).resolve().parent
STATE_PATH = BASE_DIR / "state.json"
IMAGE_DIR = BASE_DIR / "downloaded_images"
PREVIEW_DIR = BASE_DIR / "kakao_previews"
DEFAULT_KAKAO_TEXT_LIMIT = 900
DEFAULT_DEEPL_CHUNK_LIMIT = 4500
DEFAULT_TELEGRAM_TEXT_LIMIT = 3500
KAKAO_IMAGE_UPLOAD_LIMIT_BYTES = 5 * 1024 * 1024


def load_state():
    if not STATE_PATH.exists():
        return {"last_message_id": 0}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def env_required(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def env_bool(name, default=False):
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "y", "on"}


def env_int(name, default):
    value = os.getenv(name, "").strip()
    if not value:
        return default
    return int(value)


def split_text(text, limit):
    if limit <= 0:
        raise ValueError("Text split limit must be greater than 0.")

    remaining = text or ""
    chunks = []
    while len(remaining) > limit:
        split_at = max(
            remaining.rfind("\n\n", 0, limit + 1),
            remaining.rfind("\n", 0, limit + 1),
            remaining.rfind(" ", 0, limit + 1),
        )
        if split_at <= 0:
            split_at = limit
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()

    if remaining:
        chunks.append(remaining)
    return chunks or [""]


async def resolve_channel(client, channel):
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

    try:
        return await client.get_entity(channel)
    except ValueError as original_error:
        raise RuntimeError(
            "Could not find TELEGRAM_CHANNEL. Use a public @username, t.me link, "
            "numeric channel ID, or the exact chat title visible in Telegram."
        ) from original_error


def refresh_kakao_access_token():
    rest_api_key = env_required("KAKAO_REST_API_KEY")
    client_secret = os.getenv("KAKAO_CLIENT_SECRET", "").strip()
    refresh_token = env_required("KAKAO_REFRESH_TOKEN")

    data = {
        "grant_type": "refresh_token",
        "client_id": rest_api_key,
        "refresh_token": refresh_token,
    }
    if client_secret:
        data["client_secret"] = client_secret

    response = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data=data,
        timeout=20,
    )
    response.raise_for_status()
    tokens = response.json()

    access_token = tokens["access_token"]
    os.environ["KAKAO_ACCESS_TOKEN"] = access_token
    if "refresh_token" in tokens:
        os.environ["KAKAO_REFRESH_TOKEN"] = tokens["refresh_token"]
        print("Kakao returned a new refresh token. Update KAKAO_REFRESH_TOKEN in .env:")
        print(tokens["refresh_token"])

    return access_token


def post_kakao_default_message(template):
    access_token = env_required("KAKAO_ACCESS_TOKEN")
    response = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=20,
    )

    if response.status_code == 401:
        new_token = refresh_kakao_access_token()
        response = requests.post(
            "https://kapi.kakao.com/v2/api/talk/memo/default/send",
            headers={"Authorization": f"Bearer {new_token}"},
            data={"template_object": json.dumps(template, ensure_ascii=False)},
            timeout=20,
        )
        print("Kakao access token refreshed. Update KAKAO_ACCESS_TOKEN in .env:")
        print(new_token)

    response.raise_for_status()


def send_kakao_message(text, source_url=None):
    limit = env_int("KAKAO_TEXT_LIMIT", DEFAULT_KAKAO_TEXT_LIMIT)
    chunks = split_text(text, max(1, limit - 20))

    for index, chunk in enumerate(chunks, start=1):
        page_text = chunk
        if len(chunks) > 1:
            page_text = f"[{index}/{len(chunks)}]\n{chunk}"

        template = {
            "object_type": "text",
            "text": page_text,
            "link": {
                "web_url": source_url or "https://www.telegram.org",
                "mobile_web_url": source_url or "https://www.telegram.org",
            },
            "button_title": "원문 보기",
        }
        post_kakao_default_message(template)


def normalize_url_for_kakao(url):
    if not url:
        return None
    if url.startswith("http://k.kakaocdn.net/"):
        return "https://" + url[len("http://") :]
    return url


def send_kakao_image_message(title, description, image_url, source_url=None):
    image_url = normalize_url_for_kakao(image_url)
    source_url = normalize_url_for_kakao(source_url)
    link_url = source_url or "https://www.telegram.org"
    buttons = [
        {
            "title": "원문 보기",
            "link": {
                "web_url": link_url,
                "mobile_web_url": link_url,
            },
        }
    ]

    template = {
        "object_type": "feed",
        "content": {
            "title": title[:200],
            "description": description[:300],
            "image_url": image_url,
            "link": {
                "web_url": link_url,
                "mobile_web_url": link_url,
            },
        },
        "buttons": buttons,
    }
    post_kakao_default_message(template)


def extract_kakao_image_url(payload):
    if isinstance(payload, dict):
        infos = payload.get("infos")
        if isinstance(infos, dict):
            original = infos.get("original")
            if isinstance(original, dict) and original.get("url"):
                return original["url"]
        if payload.get("url"):
            return payload["url"]
    return None


def upload_image_to_kakao(local_image_path):
    app_key = (
        os.getenv("KAKAO_JAVASCRIPT_KEY", "").strip()
        or os.getenv("KAKAO_REST_API_KEY", "").strip()
    )
    if not app_key:
        return None

    local_image_path = Path(local_image_path)
    if local_image_path.stat().st_size > KAKAO_IMAGE_UPLOAD_LIMIT_BYTES:
        print(f"Skipping Kakao image upload because file is larger than 5 MB: {local_image_path}")
        return None

    content_type = mimetypes.guess_type(local_image_path.name)[0] or "application/octet-stream"
    with local_image_path.open("rb") as image_file:
        response = requests.post(
            "https://kapi.kakao.com/v2/api/talk/message/image/upload",
            params={"app_key": app_key},
            files={"file": (local_image_path.name, image_file, content_type)},
            timeout=30,
        )

    if not response.ok:
        print("Kakao image upload failed. Falling back to other image URL options.")
        print(f"HTTP {response.status_code}: {response.text[:500]}")
        return None

    return extract_kakao_image_url(response.json())


def make_uncropped_preview_image(local_image_path):
    preview_size = env_int("KAKAO_IMAGE_PREVIEW_SIZE", 800)
    local_image_path = Path(local_image_path)
    PREVIEW_DIR.mkdir(exist_ok=True)
    preview_path = PREVIEW_DIR / f"{local_image_path.stem}_preview.jpg"

    with Image.open(local_image_path) as image:
        image = ImageOps.exif_transpose(image)
        image.thumbnail((preview_size, preview_size), Image.Resampling.LANCZOS)

        canvas = Image.new("RGB", (preview_size, preview_size), "white")
        if image.mode in {"RGBA", "LA"}:
            background = Image.new("RGBA", image.size, "white")
            background.alpha_composite(image.convert("RGBA"))
            image = background.convert("RGB")
        else:
            image = image.convert("RGB")

        offset = (
            (preview_size - image.width) // 2,
            (preview_size - image.height) // 2,
        )
        canvas.paste(image, offset)
        canvas.save(preview_path, "JPEG", quality=92, optimize=True)

    return preview_path


def image_url_for_kakao(local_image_path):
    preview_path = make_uncropped_preview_image(local_image_path)
    preview_url = upload_image_to_kakao(preview_path)

    if preview_url:
        return normalize_url_for_kakao(preview_url)

    uploaded_url = upload_image_to_kakao(local_image_path)
    return normalize_url_for_kakao(uploaded_url)


def translate_with_deepl(text):
    api_key = env_required("DEEPL_API_KEY")
    api_url = os.getenv("DEEPL_API_URL", "https://api-free.deepl.com/v2/translate").strip()

    response = requests.post(
        api_url,
        headers={"Authorization": f"DeepL-Auth-Key {api_key}"},
        data={
            "text": text,
            "source_lang": "EN",
            "target_lang": "KO",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["translations"][0]["text"]


def translate_full_text(text):
    if not text:
        return ""

    chunk_limit = env_int("DEEPL_CHUNK_LIMIT", DEFAULT_DEEPL_CHUNK_LIMIT)
    translated_chunks = []
    for chunk in split_text(text, chunk_limit):
        translated_chunks.append(translate_with_deepl(chunk))
    return "\n\n".join(translated_chunks)


def build_message(original_text, translated_text, source_url=None):
    parts = [
        "[Telegram 번역]",
        "",
        translated_text,
        "",
        "[원문]",
        original_text,
    ]
    if source_url:
        parts.extend(["", source_url])
    return "\n".join(parts)


def build_translated_only_message(translated_text, source_url=None):
    parts = [
        "[Telegram 번역]",
        "",
        translated_text,
    ]
    if source_url:
        parts.extend(["", source_url])
    return "\n".join(parts)


def message_url(channel, message_id):
    if channel.startswith("@"):
        return f"https://t.me/{channel[1:]}/{message_id}"
    if channel.startswith("https://t.me/"):
        clean = channel.rstrip("/").split("/")[-1]
        if clean and not clean.startswith("+"):
            return f"https://t.me/{clean}/{message_id}"
    return None


async def download_message_image(client, message):
    if not message.media:
        return None
    IMAGE_DIR.mkdir(exist_ok=True)
    return await client.download_media(
        message,
        file=str(IMAGE_DIR / f"telegram_{message.id}_"),
    )


async def send_telegram_text(client, target_entity, text):
    limit = env_int("TELEGRAM_TEXT_LIMIT", DEFAULT_TELEGRAM_TEXT_LIMIT)
    chunks = split_text(text, max(1, limit - 20))
    for index, chunk in enumerate(chunks, start=1):
        page_text = chunk
        if len(chunks) > 1:
            page_text = f"[{index}/{len(chunks)}]\n{chunk}"
        await client.send_message(target_entity, page_text)


async def send_telegram_result(client, target_entity, translated_text, source_url=None, image_path=None):
    text = build_translated_only_message(translated_text, source_url)
    if image_path:
        caption_limit = env_int("TELEGRAM_TEXT_LIMIT", DEFAULT_TELEGRAM_TEXT_LIMIT)
        caption_chunks = split_text(text, max(1, min(1000, caption_limit - 20)))
        caption = caption_chunks[0]
        if len(caption_chunks) > 1:
            caption = f"[1/{len(caption_chunks)}]\n{caption}"
        await client.send_file(target_entity, image_path, caption=caption)
        for index, chunk in enumerate(caption_chunks[1:], start=2):
            await client.send_message(target_entity, f"[{index}/{len(caption_chunks)}]\n{chunk}")
        return

    await send_telegram_text(client, target_entity, text)


async def latest_message_id(client, channel_entity):
    async for message in client.iter_messages(channel_entity, limit=1):
        return message.id
    return 0


async def check_once(
    client,
    channel_entity,
    channel_label,
    min_text_length,
    send_existing_on_first_run,
    send_to_kakao,
    send_to_telegram,
    telegram_target_entity,
):
    state = load_state()
    last_message_id = int(state.get("last_message_id", 0))
    newest_seen_id = last_message_id

    if last_message_id == 0 and not send_existing_on_first_run:
        newest_seen_id = await latest_message_id(client, channel_entity)
        state["last_message_id"] = newest_seen_id
        save_state(state)
        print(
            "Initialized state at the latest Telegram message. "
            "Existing old messages were not sent."
        )
        return

    messages = []
    async for message in client.iter_messages(channel_entity, min_id=last_message_id, reverse=True):
        if message.id > newest_seen_id:
            newest_seen_id = message.id
        has_image = bool(message.photo)
        if not message.text and not has_image:
            continue
        text = (message.text or "").strip()
        if not has_image and len(text) < min_text_length:
            continue
        messages.append((message.id, text, has_image, message))

    for message_id, original, has_image, message in messages:
        translated = ""
        if original:
            print(f"Translating Telegram message {message_id}...")
            translated = translate_full_text(original)
        source_url = message_url(channel_label, message_id)

        image_path = None
        image_url = None
        if has_image:
            image_path = await download_message_image(client, message)
            if image_path:
                image_url = image_url_for_kakao(Path(image_path))

        if send_to_telegram and telegram_target_entity:
            telegram_text = translated or original or "텍스트 없이 이미지가 포함된 메시지입니다."
            await send_telegram_result(
                client,
                telegram_target_entity,
                telegram_text,
                source_url,
                image_path,
            )

        if send_to_kakao and image_url:
            title = "[Telegram 번역]"
            description = translated or original or "Telegram 이미지"
            send_kakao_image_message(title, description, image_url, source_url)
            if original:
                kakao_text = build_message(original, translated, source_url)
                send_kakao_message(kakao_text, source_url)
        elif send_to_kakao:
            if original:
                kakao_text = build_message(original, translated, source_url)
            else:
                kakao_text = "[Telegram 이미지]\n\n텍스트 없이 이미지가 포함된 메시지입니다."
                if source_url:
                    kakao_text += f"\n\n{source_url}"
            if image_path:
                kakao_text += f"\n\n[이미지 저장 위치]\n{image_path}"
            send_kakao_message(kakao_text, source_url)
        destinations = []
        if send_to_kakao:
            destinations.append("KakaoTalk")
        if send_to_telegram and telegram_target_entity:
            destinations.append("Telegram")
        print(f"Sent message {message_id} to {', '.join(destinations) or 'nowhere'}.")

    if newest_seen_id > last_message_id:
        state["last_message_id"] = newest_seen_id
        save_state(state)


async def main():
    load_dotenv()

    api_id = int(env_required("TELEGRAM_API_ID"))
    api_hash = env_required("TELEGRAM_API_HASH")
    phone = env_required("TELEGRAM_PHONE")
    channel = env_required("TELEGRAM_CHANNEL")
    poll_seconds = int(os.getenv("POLL_SECONDS", "20"))
    min_text_length = int(os.getenv("MIN_TEXT_LENGTH", "5"))
    send_existing_on_first_run = env_bool("SEND_EXISTING_ON_FIRST_RUN", False)
    send_to_kakao = env_bool("SEND_TO_KAKAO", True)
    send_to_telegram = env_bool("SEND_TO_TELEGRAM", False)
    telegram_target_channel = os.getenv("TELEGRAM_TARGET_CHANNEL", "").strip()
    run_once = "--once" in sys.argv

    client = TelegramClient(str(BASE_DIR / "telegram_session"), api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        raise RuntimeError(
            "Telegram session is not authorized yet. "
            "Run login_telegram.py once after Telegram code limits are cleared."
        )

    print("Started. Press Ctrl+C to stop.")
    channel_entity = await resolve_channel(client, channel)
    telegram_target_entity = None
    if send_to_telegram:
        if not telegram_target_channel:
            raise RuntimeError("SEND_TO_TELEGRAM is true, but TELEGRAM_TARGET_CHANNEL is missing.")
        telegram_target_entity = await resolve_channel(client, telegram_target_channel)
    while True:
        try:
            await check_once(
                client,
                channel_entity,
                channel,
                min_text_length,
                send_existing_on_first_run,
                send_to_kakao,
                send_to_telegram,
                telegram_target_entity,
            )
        except Exception as error:
            print(f"Error: {error}")
        if run_once:
            break
        await asyncio.sleep(poll_seconds)


if __name__ == "__main__":
    asyncio.run(main())
