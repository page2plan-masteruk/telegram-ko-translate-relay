from main import build_message, send_kakao_message, split_text, translate_full_text
from dotenv import load_dotenv


def main():
    load_dotenv()

    original = "\n\n".join(
        [
            "This is a long-message delivery test for Telegram to KakaoTalk translation.",
            "The purpose of this test is to make sure that no text is truncated when the Telegram post is longer than a single KakaoTalk message.",
            "Each paragraph should be translated, preserved, split into numbered KakaoTalk messages, and delivered in order.",
            "Markets can move quickly, and long analysis posts often include context, risk notes, trade levels, and follow-up scenarios.",
            "This sentence is repeated to create a realistic long message body. " * 35,
            "Final marker: END_OF_LONG_TEXT_TEST_2026_05_26",
        ]
    )

    translated = translate_full_text(original)
    kakao_text = "[TEST LONG TEXT]\n" + build_message(original, translated)
    parts = split_text(kakao_text, 880)

    print(f"Original length: {len(original)}")
    print(f"Translated length: {len(translated)}")
    print(f"Kakao message length: {len(kakao_text)}")
    print(f"Kakao parts: {len(parts)}")
    print(f"Max part length: {max(len(part) for part in parts)}")
    print(f"Final marker preserved: {'END_OF_LONG_TEXT_TEST_2026_05_26' in kakao_text}")

    send_kakao_message(kakao_text)
    print("Long text test sent to KakaoTalk.")


if __name__ == "__main__":
    main()
