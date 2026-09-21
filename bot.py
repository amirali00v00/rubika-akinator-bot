import os
import requests
import akinator

from flask import Flask, request


app = Flask(__name__)


# ==========================================
# تنظیمات
# ==========================================

RUBIKA_TOKEN = os.getenv("RUBIKA_TOKEN")

if not RUBIKA_TOKEN:
    raise RuntimeError("RUBIKA_TOKEN is not set")

RUBIKA_API = f"https://botapi.rubika.ir/v3/{RUBIKA_TOKEN}"

games = {}


# ==========================================
# ترجمه انگلیسی به فارسی
# ==========================================

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

        print("TRANSLATION ERROR:", repr(e))

        return text


# ==========================================
# ارسال پیام به روبیکا
# ==========================================

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

        print("SEND MESSAGE:")
        print(response.status_code)
        print(response.text)

        return response.json()

    except Exception as e:

        print("SEND MESSAGE ERROR:", repr(e))

        return None


# ==========================================
# دکمه‌های شیشه‌ای
# ==========================================

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


# ==========================================
# تست اتصال Akinator
# ==========================================

def start_game(chat_id):

    print("\n================================")
    print("STARTING AKINATOR")
    print("CHAT:", chat_id)
    print("================================")

    try:

        print("1) Creating Akinator object...")

        aki = akinator.Akinator()

        print("2) Akinator object created.")

        print("3) Calling start_game()...")

        try:

            aki.start_game()

            print("4) AKINATOR GAME STARTED!")

        except Exception as e:

            print(
                "4) AKINATOR START EXCEPTION:",
                repr(e)
            )

            raise


        print("5) Question received:")
        print(repr(aki.question))


        games[chat_id] = aki


        print("6) Translating question...")

        question = translate_to_persian(
            aki.question
        )


        print("7) Translation result:")
        print(repr(question))


        message = (
            "🧠 بازی Akinator شروع شد!\n\n"
            "به یک شخصیت فکر کن و به سؤال‌ها جواب بده.\n\n"
            f"❓ {question}"
        )


        print("8) Sending first question...")

        send_message(
            chat_id,
            message,
            answer_keypad()
        )


        print("9) FIRST QUESTION SENT!")


    except Exception as e:

        print("\n!!!!!!!!!!!!!!!!!!!!!!!!")
        print("AKINATOR START ERROR:")
        print(repr(e))
        print("TYPE:", type(e).__name__)
        print("!!!!!!!!!!!!!!!!!!!!!!!!\n")


        send_message(
            chat_id,
            "❌ نتونستم بازی رو شروع کنم.\n\n"
            "اتصال Akinator روی سرور با مشکل مواجه شد.\n"
            "لطفاً دوباره /start رو امتحان کن."
        )


# ==========================================
# پاسخ به Akinator
# ==========================================

def process_answer(chat_id, answer):

    print("\n================================")
    print("PROCESS ANSWER")
    print("CHAT:", chat_id)
    print("ANSWER:", answer)
    print("================================")


    aki = games.get(chat_id)


    if aki is None:

        send_message(
            chat_id,
            "⚠️ بازی فعالی وجود نداره.\n\n"
            "برای شروع /start رو بفرست."
        )

        return


    try:

        print("Calling aki.answer()...")

        aki.answer(answer)

        print("Answer processed.")


        # ==================================
        # پایان بازی
        # ==================================

        if aki.finished:

            print("AKINATOR FINISHED!")


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


            message = (
                "🎯 فکر کنم فهمیدم!\n\n"
                f"👤 شخصیت: {name}\n"
            )


            if description:

                message += (
                    f"\n📝 توضیح:\n"
                    f"{description}\n"
                )


            if photo:

                message += (
                    f"\n🖼️ عکس:\n"
                    f"{photo}\n"
                )


            message += (
                "\n\n"
                "اگر درست حدس نزدم، "
                "روی «🔄 شروع دوباره» بزن."
            )


            send_message(
                chat_id,
                message,
                answer_keypad()
            )


            return


        # ==================================
        # سؤال بعدی
        # ==================================

        print("Getting next question...")

        question = translate_to_persian(
            aki.question
        )


        send_message(
            chat_id,
            f"❓ {question}",
            answer_keypad()
        )


    except Exception as e:

        print("\n!!!!!!!!!!!!!!!!!!!!!!!!")
        print("AKINATOR ANSWER ERROR:")
        print(repr(e))
        print("TYPE:", type(e).__name__)
        print("!!!!!!!!!!!!!!!!!!!!!!!!\n")


        games.pop(
            chat_id,
            None
        )


        send_message(
            chat_id,
            "❌ هنگام پردازش جواب مشکلی پیش اومد.\n\n"
            "لطفاً /start رو بزن."
        )


# ==========================================
# Webhook روبیکا
# ==========================================

@app.route(
    "/webhook",
    methods=["POST"]
)
def webhook():

    update = request.get_json(
        silent=True
    ) or {}


    print("\n")
    print("========== UPDATE ==========")
    print(update)
    print("============================")
    print("\n")


    update_data = update.get(
        "update"
    ) or {}


    new_message = update_data.get(
        "new_message"
    ) or {}


    chat_id = update_data.get(
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


    print("CHAT ID:", chat_id)
    print("TEXT:", text)
    print("BUTTON ID:", button_id)


    if not chat_id:

        print("NO CHAT ID!")

        return "OK"


    # ======================================
    # دکمه‌های شیشه‌ای
    # ======================================

    if button_id:

        print(
            "BUTTON CLICKED:",
            button_id
        )


        if button_id == "restart":

            print("RESTART GAME")

            games.pop(
                chat_id,
                None
            )

            start_game(
                chat_id
            )

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


    # ======================================
    # پیام متنی
    # ======================================

    if text:

        clean_text = text.strip().lower()


        if clean_text in [
            "/start",
            "start",
            "/شروع"
        ]:

            print("START COMMAND RECEIVED")


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

            print("STOP COMMAND RECEIVED")


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


# ==========================================
# صفحه اصلی
# ==========================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return "🧠 Rubika Akinator Bot is running!"


# ==========================================
# اجرای برنامه
# ==========================================

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
