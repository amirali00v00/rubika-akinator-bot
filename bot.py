import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.getenv("RUBIKA_TOKEN")

API = f"https://botapi.rubika.ir/v3/{TOKEN}"


def send_message(chat_id, text):
    url = f"{API}/sendMessage"

    inline_keypad = {
        "rows": [
            {
                "buttons": [
                    {
                        "id": "yes",
                        "type": "Simple",
                        "button_text": "✅ بله"
                    },
                    {
                        "id": "no",
                        "type": "Simple",
                        "button_text": "❌ خیر"
                    }
                ]
            },
            {
                "buttons": [
                    {
                        "id": "unknown",
                        "type": "Simple",
                        "button_text": "🤷 نمی‌دانم"
                    }
                ]
            },
            {
                "buttons": [
                    {
                        "id": "probably",
                        "type": "Simple",
                        "button_text": "🤔 احتمالاً"
                    },
                    {
                        "id": "probably_no",
                        "type": "Simple",
                        "button_text": "🙅 احتمالاً خیر"
                    }
                ]
            }
        ]
    }

    data = {
        "chat_id": chat_id,
        "text": text,
        "inline_keypad": inline_keypad
    }

    return requests.post(url, json=data, timeout=15).json()


@app.route("/", methods=["GET"])
def home():
    return "Rubika Akinator Bot is running!"


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}

    print("UPDATE:")
    print(update)

    inline = update.get("inline_message", {})

    chat_id = inline.get("chat_id")
    text = inline.get("text", "")
    aux_data = inline.get("aux_data") or {}
    button_id = aux_data.get("button_id")

    if not chat_id:
        return "OK"

    if button_id:
        responses = {
            "yes": "✅ بله انتخاب شد",
            "no": "❌ خیر انتخاب شد",
            "unknown": "🤷 نمی‌دانم انتخاب شد",
            "probably": "🤔 احتمالاً انتخاب شد",
            "probably_no": "🙅 احتمالاً خیر انتخاب شد"
        }

        send_message(
            chat_id,
            responses.get(button_id, "دکمه ناشناخته است")
        )

    elif text == "/start":
        send_message(
            chat_id,
            "🧠 به ربات Akinator خوش آمدی!\n\n"
            "این فقط نسخه آزمایشی دکمه‌هاست."
        )

    return "OK"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
