import json
import os

import requests
from dotenv import load_dotenv


def env_required(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is missing in .env")
    return value


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

    print("A new Kakao access token was issued.")
    print("Copy this into .env:")
    print(f"KAKAO_ACCESS_TOKEN={tokens['access_token']}")

    if "refresh_token" in tokens:
        print()
        print("Kakao also returned a new refresh token. Copy this into .env too:")
        print(f"KAKAO_REFRESH_TOKEN={tokens['refresh_token']}")

    return tokens["access_token"]


def send_test_message(access_token):
    template = {
        "object_type": "text",
        "text": "카카오 나에게 보내기 테스트입니다.\nTelegram 번역 자동화 준비 중입니다.",
        "link": {
            "web_url": "https://developers.kakao.com/",
            "mobile_web_url": "https://developers.kakao.com/",
        },
        "button_title": "Kakao Developers",
    }

    return requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=20,
    )


def main():
    load_dotenv()

    access_token = env_required("KAKAO_ACCESS_TOKEN")
    response = send_test_message(access_token)

    if response.status_code == 401:
        print("Kakao access token is expired or invalid. Trying refresh token...")
        access_token = refresh_kakao_access_token()
        response = send_test_message(access_token)

    if not response.ok:
        print("Kakao test failed.")
        print(f"HTTP {response.status_code}")
        print(response.text)
        raise SystemExit(1)

    print("Kakao test succeeded. Check your KakaoTalk.")


if __name__ == "__main__":
    main()
