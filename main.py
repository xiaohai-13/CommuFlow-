"""CommuFlow - Flask webhook entry"""
import json
from datetime import datetime
from flask import Flask, request, jsonify
from agent.graph import run_agent
from utils.feishu_client import feishu
from utils.logger import logger
from utils.task_manager import init_db

app = Flask(__name__)
processed_ids = set()
TODAY = datetime.now().strftime("%Y-%m-%d")


@app.route("/", methods=["GET"])
def health():
    return "CommuFlow is running"


@app.route("/feishu/event", methods=["POST"])
def feishu_event():
    body = request.get_json(force=True, silent=True) or {}

    if body.get("type") == "url_verification":
        return jsonify({"challenge": body.get("challenge", "")})

    header = body.get("header", {})
    event = body.get("event", {})
    event_type = header.get("event_type", "")

    if event_type == "im.message.receive_v1":
        # v1 event: message fields are directly under event
        # v2 compat: try event.message first, fallback to event
        message = event.get("message", event)

        message_id = message.get("message_id", "")
        if message_id in processed_ids:
            return jsonify({"code": 0})
        processed_ids.add(message_id)
        if len(processed_ids) > 1000:
            processed_ids.clear()

        if message.get("message_type") == "text" or message.get("msg_type") == "text":
            raw = json.loads(message.get("content", "{}"))
            text = raw.get("text", "")

            # Parse mentions: try message.mentions first (v2), then event.mentions (v1)
            mentions = message.get("mentions") or event.get("mentions") or []
            mention_map = {}
            for m in mentions:
                key = m.get("key", "")
                name = m.get("name", "")
                mid = m.get("id") or {}
                open_id = mid.get("open_id", "")
                if key and name:
                    mention_map[key] = {"name": name, "open_id": open_id}

            for key, info in mention_map.items():
                text = text.replace(key, f"@{info['name']}")

            sender_id = event.get("sender", {}).get("sender_id", {}).get("open_id", "")
            chat_id = message.get("chat_id", "")

            logger.info(f"msg: sender={sender_id}, text={text[:80]}, mention_count={len(mention_map)}")

            if text and sender_id:
                try:
                    reply = run_agent(
                        user_id=sender_id, chat_id=chat_id,
                        text=text, mention_map=mention_map
                    )
                    feishu.reply_message(message_id, reply)
                    logger.info(f"reply: {reply[:80]}")
                except Exception as e:
                    logger.error(f"error: {e}")
                    feishu.reply_message(message_id, "系统异常，请稍后重试")

    return jsonify({"code": 0})


if __name__ == "__main__":
    init_db()
    logger.info(f"CommuFlow starting on :5000 (today={TODAY})")
    app.run(host="0.0.0.0", port=5000, debug=False)