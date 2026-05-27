import os

import requests
from dotenv import load_dotenv


def main():
    load_dotenv()

    api_key = os.getenv("DEEPL_API_KEY", "").strip()
    api_url = os.getenv("DEEPL_API_URL", "https://api-free.deepl.com/v2/translate").strip()

    if not api_key:
        raise SystemExit("DEEPL_API_KEY is missing in .env")

    response = requests.post(
        api_url,
        headers={"Authorization": f"DeepL-Auth-Key {api_key}"},
        data={
            "text": "Hello, this is a translation test.",
            "source_lang": "EN",
            "target_lang": "KO",
        },
        timeout=30,
    )

    if not response.ok:
        print("DeepL test failed.")
        print(f"HTTP {response.status_code}")
        print(response.text)
        raise SystemExit(1)

    translated = response.json()["translations"][0]["text"]
    print("DeepL test succeeded.")
    print(translated)


if __name__ == "__main__":
    main()
