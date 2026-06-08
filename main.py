"""CommuFlow - Flask webhook entry with Feishu event normalization layer"""
import json
from datetime import datetime
from flask import Flask, request, jsonify
from agent.graph import run_agent
from utils.feishu_client import feishu
from utils.logger import logger
from utils.task_manager import init_db

app = Flask(__name__)
processed_ids = set()

# ═══════════════════════════════════════════════════════════
#  Normalization layer: Feishu event → consistent internal format
#  Handles REST API (string ids) and v1 events (nested ids)
# ═══════════════════════════════════════════════════════════


def _extract_str(value) -> str:
    """Normalize a value that might be a string or nested {'open_id':'...','user_id':null}"""
    if isinstance(value, dict):
        return str(value.get("open_id", value.get("id", "")) or "")
    return str(value) if value else ""


def _normalize_sender(sender: dict) -> str:
    """Extract sender open_id from Feishu event. Handles:
    - REST API: sender.id = 'ou_xxx'
    - v1 event: sender.sender_id.open_id = 'ou_xxx'
    - v1 event: sender.sender_id = {'open_id':'ou_xxx','user_id':null}
    """
    # v1 nested path
    sender_id_node = sender.get("sender_id")
    if sender_id_node:
        return _extract_str(sender_id_node)
    # REST API or flat structure
    return _extract_str(sender.get("id", ""))


def _normalize_mentions(mentions: list) -> dict:
    """Normalize mentions to {key: {name, open_id}}.
    Handles:
    - REST API: id = 'ou_xxx' (string)
    - v1 event: id = {'open_id':'ou_xxx','user_id':null} (dict)
    """
    result = {}
    for m in mentions:
        key = m.get("key", "")
        name = m.get("name", "")
        open_id = _extract_str(m.get("id", ""))
        if key and name and open_id:
            result[key] = {"name": name, "open_id": open_id}
    return result


def _extract_text(message: dict) -> str:
    """Extract plain text from message body. Handles:
    - body.content = '{"text":"..."}' (JSON string)
    - content = '{"text":"..."}' (direct)
    """
    body_node = message.get("body", {})
    raw = body_node.get("content") or message.get("content", "{}")
    try:
        return json.loads(raw).get("text", "")
    except (json.JSONDecodeError, TypeError):
        return ""


def _replace_mentions(text: str, mention_map: dict) -> str:
    """Replace @_user_X placeholders with @display_name"""
    for key, info in mention_map.items():
        text = text.replace(key, f"@{info['name']}")
    return text


def _dedup(message_id: str) -> bool:
    """Return True if already processed, False otherwise"""
    if message_id in processed_ids:
        return True
    processed_ids.add(message_id)
    if len(processed_ids) > 5000:
        processed_ids.clear()
    return False


# ═══════════════════════════════════════════════════════════
#  Routes
# ═══════════════════════════════════════════════════════════


@app.route("/", methods=["GET"])
def health():
    return "CommuFlow is running"


@app.route("/feishu/event", methods=["POST"])
def feishu_event():
    body = request.get_json(force=True, silent=True) or {}

    # URL verification handshake
    if body.get("type") == "url_verification":
        return jsonify({"challenge": body.get("challenge", "")})

    header = body.get("header", {})
    event = body.get("event", {})
    event_type = header.get("event_type", "")

    if event_type != "im.message.receive_v1":
        return jsonify({"code": 0})

    # ── Normalize ──
    message = event.get("message", event)
    message_id = message.get("message_id", "")

    if _dedup(message_id):
        return jsonify({"code": 0})

    msg_type = message.get("msg_type") or message.get("message_type", "")
    if msg_type != "text":
        return jsonify({"code": 0})

    text = _extract_text(message)
    mention_map = _normalize_mentions(message.get("mentions", []))
    text = _replace_mentions(text, mention_map)
    sender_id = _normalize_sender(event.get("sender", {}))
    chat_id = message.get("chat_id", "")

    logger.info(f"msg: sender={sender_id}, text={text[:80]}, mentions={len(mention_map)}")

    if not text or not sender_id:
        return jsonify({"code": 0})

    # ── Agent ──
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
    logger.info(f"CommuFlow starting on :5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
