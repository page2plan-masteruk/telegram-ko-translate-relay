import os

from dotenv import load_dotenv


REQUIRED_KEYS = [
    "TELEGRAM_API_ID",
    "TELEGRAM_API_HASH",
    "TELEGRAM_PHONE",
    "TELEGRAM_CHANNEL",
    "DEEPL_API_KEY",
    "DEEPL_API_URL",
    "KAKAO_REST_API_KEY",
    "KAKAO_REDIRECT_URI",
    "KAKAO_ACCESS_TOKEN",
    "KAKAO_REFRESH_TOKEN",
]

OPTIONAL_KEYS = [
    "KAKAO_CLIENT_SECRET",
    "KAKAO_JAVASCRIPT_KEY",
    "POLL_SECONDS",
    "MIN_TEXT_LENGTH",
    "SEND_EXISTING_ON_FIRST_RUN",
    "SEND_TO_KAKAO",
    "SEND_TO_TELEGRAM",
    "TELEGRAM_TARGET_CHANNEL",
    "TELEGRAM_TEXT_LIMIT",
    "KAKAO_TEXT_LIMIT",
    "DEEPL_CHUNK_LIMIT",
    "KAKAO_IMAGE_PREVIEW_SIZE",
]


def status_for(key):
    value = os.getenv(key, "").strip()
    if not value:
        return "missing"
    return f"set ({len(value)} chars)"


def main():
    load_dotenv()

    missing = []
    print("Required settings:")
    for key in REQUIRED_KEYS:
        status = status_for(key)
        print(f"- {key}: {status}")
        if status == "missing":
            missing.append(key)

    print()
    print("Optional settings:")
    for key in OPTIONAL_KEYS:
        print(f"- {key}: {status_for(key)}")

    if missing:
        print()
        print("Missing required settings:")
        for key in missing:
            print(f"- {key}")
        raise SystemExit(1)

    print()
    print(".env looks ready. Secret values were not printed.")


if __name__ == "__main__":
    main()
