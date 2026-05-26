# Telegram Korean Translation Relay

A Python automation tool that translates new messages from an English Telegram channel into Korean using DeepL, then forwards them to a separate Telegram translation channel and optionally to KakaoTalk Send to Me.

It supports long-text splitting, Telegram image forwarding, and KakaoTalk image cards.

## Features

- Read messages from a Telegram channel or chat your account can access
- Translate English text to Korean with DeepL
- Forward translated messages to a separate Telegram channel
- Optionally send alerts to KakaoTalk Send to Me
- Forward Telegram photo messages with translated captions
- Split long messages so they are not truncated
- Keep local state to avoid sending the same message twice

## Project Files

| File | Purpose |
| --- | --- |
| `main.py` | Main polling and forwarding script |
| `login_telegram.py` | Creates a local Telegram session |
| `get_kakao_tokens.py` | Issues Kakao OAuth tokens |
| `create_telegram_target.py` | Creates a private Telegram target channel |
| `validate_env.py` | Checks required settings without printing secrets |
| `test_*.py` | Small end-to-end test scripts |
| `BEGINNER_GUIDE_KO.html` | Korean beginner guide |
| `TROUBLESHOOTING_KO.html` | Korean troubleshooting guide |
| `DESIGN.md` | Architecture and API checklist |

## Requirements

- Python 3.10+
- Telegram account
- Telegram API ID and hash from <https://my.telegram.org>
- DeepL API key
- Optional: Kakao Developers app for KakaoTalk Send to Me

## Installation

```powershell
git clone https://github.com/YOUR_GITHUB_USERNAME/telegram-ko-translate-relay.git
cd telegram-ko-translate-relay

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks virtual environment activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Configuration

Create a local `.env` file:

```powershell
Copy-Item .env.template .env
```

Then fill in your own values.

```dotenv
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_PHONE=
TELEGRAM_CHANNEL=
TELEGRAM_TARGET_CHANNEL=

DEEPL_API_KEY=
DEEPL_API_URL=https://api-free.deepl.com/v2/translate

SEND_TO_TELEGRAM=true
SEND_TO_KAKAO=false

KAKAO_REST_API_KEY=
KAKAO_REDIRECT_URI=http://localhost:8000/callback
KAKAO_ACCESS_TOKEN=
KAKAO_REFRESH_TOKEN=
```

Never commit your real `.env` file.

## Telegram Setup

1. Go to <https://my.telegram.org>
2. Create an app and copy `api_id` and `api_hash`
3. Put them into `.env`
4. Log in once:

```powershell
python login_telegram.py
```

List accessible chats and channels:

```powershell
python list_telegram_chats.py
```

Use numeric channel IDs when possible. They are more stable than display names.

If you need a new private Korean translation channel:

```powershell
python create_telegram_target.py
```

Copy the printed ID into:

```dotenv
TELEGRAM_TARGET_CHANNEL=
```

## DeepL Setup

1. Create a DeepL API account
2. Copy your API key into `.env`
3. Use the free API endpoint unless you are on DeepL Pro:

```dotenv
DEEPL_API_URL=https://api-free.deepl.com/v2/translate
```

## KakaoTalk Setup

KakaoTalk forwarding is optional.

To enable it:

```dotenv
SEND_TO_KAKAO=true
```

Then:

1. Create an app at <https://developers.kakao.com>
2. Enable Kakao Login
3. Add this redirect URI:

```text
http://localhost:8000/callback
```

4. Enable the KakaoTalk message permission, usually `talk_message`
5. Run:

```powershell
python get_kakao_tokens.py
```

6. Copy the generated tokens into `.env`

## Validation

```powershell
python validate_env.py
```

Expected result:

```text
.env looks ready. Secret values were not printed.
```

## Tests

Run individual checks:

```powershell
python test_telegram.py
python test_telegram_target.py
python test_deepl.py
python test_kakao.py
python test_dual_pipeline.py
python test_telegram_image_target.py
python test_long_text.py
```

## Run

```powershell
python main.py
```

Run one polling cycle only:

```powershell
python main.py --once
```

Stop with:

```text
Ctrl + C
```

## Security

Do not commit or share:

- `.env`
- `telegram_session.session`
- `telegram_session.session-journal`
- `state.json`
- `downloaded_images/`
- `kakao_previews/`
- `.venv/`

If any token or session file leaks, revoke the related Telegram, Kakao, or DeepL credentials immediately.

## License

MIT
