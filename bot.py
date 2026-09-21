import os
import requests
import akinator

from flask import Flask, request


app = Flask(__name__)


# =========================
# تنظیمات
# =========================

RUBIKA_TOKEN = os.getenv("RUBIKA_TOKEN")

if not RUBIKA_TOKEN:
    raise RuntimeError("RUBIKA_TOKEN environment variable is not set")


RUBIKA_API = f"https://botapi.rubika.ir/v3/{RUBIKA_TOKEN}"


# هر کاربر یک بازی جداگانه دارد
games = {}


# =========================
# ترجمه انگلیسی به فارسی
# =========================

def translate_to_persian(text):
    url = "https://api.mymemory.translated.net/get"

    params = {
        "q": text,
        "langpair": "en|fa"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        return data["responseData"]["translatedText"]

    except Exception as e:
        print("Translation error:", e)

        # اگر ترجمه شکست خورد، حداقل سؤال انگلیسی را از دست ندهیم
        return text


# =========================
# ارسال پیام به روبیکا
# =========================

def send_message(chat_id, text, inline_keypad=None):

    url = f"{RUBIKA_API}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if inline_keypad:
        data["inline_keypad"] = inline_keypad

    try:
        response = requests.post(
            url,
            json=data,
            timeout=15
        )

        print("Rubika response:", response.text)

        return response.json()

    except Exception as e:
        print("Rubika send error:", e)
        return None


# =========================
# دکمه‌های شیشه‌ای پاسخ
# =========================

def answer_keypad():

    return {
        "rows": [
            {
                "buttons": [
                    {
                        "id": "answer_yes",
                        "type": "Simple",
                        "button_text": "✅ بله"
                    },
                    {
                        "id": "answer_no",
                        "type": "Simple",
                        "button_text": "❌ خیر"
                    }
                ]
            },
            {
                "buttons": [
                    {
                        "id": "answer_idk",
                        "type": "Simple",
                        "button_text": "🤷 نمی‌دانم"
                    }
                ]
            },
            {
                "buttons": [
                    {
                        "id": "answer_probably",
                        "type": "Simple",
                        "button_text": "🤔 احتمالاً"
                    },
                    {
                        "id": "answer_probably_no",
                        "type": "Simple",
                        "button_text": "🙅 احتمالاً خیر"
                    }
                ]
            },
            {
                "buttons": [
                    {
                        "id": "restart",
                        "type": "Simple",
                        "button_text": "🔄 شروع دوباره"
                    }
                ]
            }
        ]
    }


# =========================
# شروع بازی
# =========================

def start_game(chat_id):

    try:

        print(f"Starting Akinator game for {chat_id}")

        aki = akinator.Akinator()

        aki.start_game()

        games[chat_id] = aki

        question = translate_to_persian(aki.question)

        text = (
            "🧠 بازی Akinator شروع شد!\n\n"
            "به یک شخصیت فکر کن و به سؤال‌ها جواب بده.\n\n"
            f"❓ {question}"
        )

        send_message(
            chat_id,
            text,
            answer_keypad()
        )

    except Exception as e:

        print("Akinator start error:", e)

        send_message(
            chat_id,
            "❌ متأسفانه نتونستم بازی رو شروع کنم.\n"
            "چند لحظه بعد دوباره امتحان کن."
        )


# =========================
# پاسخ به سؤال Akinator
# =========================

def process_answer(chat_id, answer):

    aki = games.get(chat_id)

    if aki is None:

        send_message(
            chat_id,
            "⚠️ هنوز بازی‌ای شروع نکردی.\n"
            "اول /start رو بفرست."
        )

        return


    try:

        print(
            f"User {chat_id} answered: {answer}"
        )

        aki.answer(answer)

        # آیا Akinator به حدس رسیده؟
        if aki.finished:

            name = getattr(
                aki,
                "name_proposition",
                "نامشخص"
            )

            description = getattr(
                aki,
                "description_proposition",
                ""
            )

            photo = getattr(
                aki,
                "photo",
                ""
            )

            text = (
                "🎯 فکر کنم فهمیدم!\n\n"
                f"👤 شخصیت: {name}\n"
            )

            if description:
                text += f"\n📝 توضیح:\n{description}\n"

            if photo:
                text += f"\n🖼️ عکس:\n{photo}\n"

            text += (
                "\n\n"
                "اگر درست حدس نزدم، فعلاً می‌تونی "
                "با «🔄 شروع دوباره» یک بازی جدید شروع کنی."
            )

            send_message(
                chat_id,
                text,
                answer_keypad()
            )

            return


        # سؤال بعدی
        question = translate_to_persian(
            aki.question
        )

        text = (
            f"❓ {question}"
        )

        send_message(
            chat_id,
            text,
            answer_keypad()
        )

    except Exception as e:

        print("Akinator answer error:", e)

        send_message(
            chat_id,
            "❌ هنگام ارتباط با Akinator مشکلی پیش اومد.\n"
            "لطفاً دوباره /start رو بزن."
        )

        games.pop(chat_id, None)


# =========================
# دریافت Webhook روبیکا
# =========================

@app.route("/webhook", methods=["POST"])
def webhook():

    update = request.get_json(
        silent=True
    ) or {}

    print("\n========== UPDATE ==========")
    print(update)
    print("============================\n")


    # --------------------------------
    # حالت inline_message
    # --------------------------------

    inline = update.get("inline_message")

    if inline:

        chat_id = inline.get("chat_id")

        text = inline.get("text", "")

        aux_data = inline.get(
            "aux_data"
        ) or {}

        button_id = aux_data.get(
            "button_id"
        )


    # --------------------------------
    # حالت update.new_message
    # --------------------------------

    else:

        update_data = update.get(
            "update"
        ) or {}

        new_message = update_data.get(
            "new_message"
        ) or {}

        chat_id = new_message.get(
            "chat_id"
        )

        text = new_message.get(
            "text",
            ""
        )

        aux_data = new_message.get(
            "aux_data"
        ) or {}

        button_id = aux_data.get(
            "button_id"
        )


    if not chat_id:
        return "OK"


    # =========================
    # دکمه‌ها
    # =========================

    if button_id:

        if button_id == "restart":

            games.pop(
                chat_id,
                None
            )

            start_game(chat_id)

            return "OK"


        answers = {

            "answer_yes": "y",

            "answer_no": "n",

            "answer_idk": "i",

            "answer_probably": "p",

            "answer_probably_no": "pn"

        }


        answer = answers.get(
            button_id
        )


        if answer:

            process_answer(
                chat_id,
                answer
            )


        return "OK"


    # =========================
    # پیام متنی
    # =========================

    if text:

        clean_text = text.strip().lower()


        if clean_text in [
            "/start",
            "start",
            "/شروع"
        ]:

            games.pop(
                chat_id,
                None
            )

            start_game(
                chat_id
            )

            return "OK"


        if clean_text in [
            "/stop",
            "/خروج"
        ]:

            games.pop(
                chat_id,
                None
            )

            send_message(
                chat_id,
                "🛑 بازی متوقف شد.\n\n"
                "برای شروع دوباره /start رو بزن."
            )

            return "OK"


        send_message(
            chat_id,
            "🧠 برای شروع بازی /start رو بفرست."
        )


    return "OK"


# =========================
# تست سلامت Render
# =========================

@app.route("/", methods=["GET"])
def home():

    return "🧠 Rubika Akinator Bot is running!"


# =========================
# اجرای برنامه
# =========================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
        )
