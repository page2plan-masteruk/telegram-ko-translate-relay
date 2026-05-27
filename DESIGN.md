# Telegram English to KakaoTalk Korean Translator

## Goal

Receive new English messages from a Telegram channel or chat, translate them into Korean, and send the translated result to your KakaoTalk using Kakao's "Send me" API.

## Architecture

```text
Telegram channel/chat
  -> Telethon client using your Telegram account session
  -> main.py polling loop
  -> DeepL Translate API
  -> KakaoTalk "Send me" message API
  -> Your KakaoTalk
```

## Required Accounts and API Keys

| Service | Required values | Where to get them |
| --- | --- | --- |
| Telegram | `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`, `TELEGRAM_CHANNEL` | https://my.telegram.org |
| DeepL | `DEEPL_API_KEY`, `DEEPL_API_URL` | https://www.deepl.com/pro-api |
| Kakao | `KAKAO_REST_API_KEY`, optional `KAKAO_CLIENT_SECRET`, `KAKAO_ACCESS_TOKEN`, `KAKAO_REFRESH_TOKEN` | https://developers.kakao.com |

## Runtime Flow

1. `login_telegram.py` creates `telegram_session.session` after one successful Telegram login.
2. `get_kakao_tokens.py` opens a local OAuth callback server and issues Kakao access and refresh tokens.
3. `main.py` checks Telegram every `POLL_SECONDS`.
4. New text messages after `state.json:last_message_id` are translated from English to Korean.
5. The Korean translation, English original, and a Telegram source link are sent to KakaoTalk.
6. Long Telegram text is translated in chunks and sent to KakaoTalk in numbered parts so it is not truncated.
7. If the Telegram message contains a photo, the image is saved to `downloaded_images`.
8. The script creates a padded preview image in `kakao_previews` so KakaoTalk does not crop the image card badly.
9. The padded preview is uploaded to Kakao's image server and sent as a KakaoTalk image card.
10. `state.json` is updated so the same Telegram message is not sent twice.

## Files

| File | Purpose |
| --- | --- |
| `main.py` | Main automation loop |
| `login_telegram.py` | One-time Telegram account login |
| `get_kakao_tokens.py` | One-time Kakao OAuth token issuer |
| `test_telegram.py` | Confirms Telegram channel access |
| `list_telegram_chats.py` | Lists accessible Telegram channel/group titles, usernames, and IDs |
| `test_deepl.py` | Confirms DeepL translation |
| `test_kakao.py` | Confirms KakaoTalk send-me messaging |
| `test_pipeline.py` | Sends one latest Telegram message through translation to KakaoTalk as a test |
| `test_image_pipeline.py` | Finds one recent Telegram photo, downloads it, and sends the Kakao notification |
| `validate_env.py` | Confirms `.env` has the required keys without printing secrets |
| `state.json` | Last processed Telegram message ID |

## Security Notes

Never share `.env`, `telegram_session.session`, or Kakao tokens. They grant access to your Telegram session or Kakao message permission. If any secret leaks, revoke it in the relevant developer console and issue a new one.

## Operational Notes

This project uses polling instead of webhooks because it reads messages through your own Telegram account session. Keep `main.py` running on a trusted PC or server. For long-running use, run it on a VPS, Windows Task Scheduler, or another always-on environment.

By default, `main.py` initializes `state.json` at the newest Telegram message on first run, so old messages are not sent in bulk. Set `SEND_EXISTING_ON_FIRST_RUN=true` only if you intentionally want to send the backlog.
