import json
import hashlib
from flask import Flask, request, jsonify
from config import FEISHU_VERIFY_TOKEN, FLASK_HOST, FLASK_PORT
from db.database import init_db
from bot.router import route_message
from feishu.client import feishu

app = Flask(__name__)


@app.route("/", methods=["GET"])
def health():
    return "CommuFlow is running"


@app.route("/feishu/event", methods=["POST"])
def feishu_event():
    body = request.get_json(force=True, silent=True) or {}

    if body.get("type") == "url_verification":
        token = body.get("token", "")
        challenge = body.get("challenge", "")
        if token == FEISHU_VERIFY_TOKEN:
            return jsonify({"challenge": challenge})
        return jsonify({"challenge": ""})

    header = body.get("header", {})
    event = body.get("event", {})
    event_type = header.get("event_type", "")

    if event_type == "im.message.receive_v1":
        message = event.get("message", {})
        msg_type = message.get("message_type", "")

        if msg_type == "text":
            content = json.loads(message.get("content", "{}"))
            text = content.get("text", "").replace("@_user_1", "").strip()

            sender = event.get("sender", {})
            sender_id = sender.get("sender_id", {}).get("open_id", "")
            sender_name = sender.get("sender_id", {}).get("open_id", "")

            chat_id = message.get("chat_id", "")
            message_id = message.get("message_id", "")

            if text:
                try:
                    sender_name = feishu.get_user_info(sender_id).get("name", sender_name)
                except Exception:
                    pass

                reply = route_message(text, sender_id, sender_name, chat_id, message_id)
                feishu.reply_message(message_id, reply)

    return jsonify({"code": 0})


if __name__ == "__main__":
    init_db()
    print(f"CommuFlow starting on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
