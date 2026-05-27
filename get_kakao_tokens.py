import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from dotenv import load_dotenv


load_dotenv()


REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "").strip()
CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", "").strip()
REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8000/callback").strip()


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", [""])[0]

        if not code:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No code parameter found.")
            return

        token_url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": REST_API_KEY,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        }
        if CLIENT_SECRET:
            data["client_secret"] = CLIENT_SECRET
        response = requests.post(token_url, data=data, timeout=20)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

        if not response.ok:
            self.wfile.write(response.text.encode("utf-8"))
            return

        tokens = response.json()
        message = (
            "Kakao token issued.\n\n"
            "Copy these values into your .env file:\n\n"
            f"KAKAO_ACCESS_TOKEN={tokens.get('access_token', '')}\n"
            f"KAKAO_REFRESH_TOKEN={tokens.get('refresh_token', '')}\n"
        )
        self.wfile.write(message.encode("utf-8"))

    def log_message(self, format, *args):
        return


def main():
    if not REST_API_KEY:
        raise SystemExit("KAKAO_REST_API_KEY is missing in .env")

    auth_params = {
        "client_id": REST_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "talk_message",
    }
    auth_url = "https://kauth.kakao.com/oauth/authorize?" + urllib.parse.urlencode(auth_params)

    print("1. Open this URL in your browser:")
    print(auth_url)
    print()
    print("2. Log in with Kakao and approve the permission.")
    print("3. Keep this program running until the callback page appears.")
    print()
    print("Waiting on http://localhost:8000/callback ...")

    server = HTTPServer(("localhost", 8000), CallbackHandler)
    server.handle_request()


if __name__ == "__main__":
    main()
