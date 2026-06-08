"""CommuFlow - Feishu long connection entry"""
import json
import os
import time
from lark_oapi import Client, Config, LOGGER
from lark_oapi.event.processor import set_event_callback
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1
from agent.graph import run_agent
from utils.feishu_client import feishu
from utils.config import FEISHU_APP_ID, FEISHU_APP_SECRET
from utils.logger import logger
from agent.rag import init_rag


def on_message_received(event: P2ImMessageReceiveV1):
    """Callback when message received"""
    msg = event.event.message
    if msg.msg_type != "text":
        return

    content = json.loads(msg.content).get("text", "")
    if not content:
        return

    sender = event.event.sender
    sender_id = sender.sender_id.open_id or ""
    chat_id = msg.chat_id

    logger.info(f"msg from {sender_id} in {chat_id}: {content[:50]}")

    try:
        reply = run_agent(user_id=sender_id, chat_id=chat_id, text=content)
        feishu.reply_message(msg.message_id, reply)
        logger.info(f"reply: {reply[:80]}")
    except Exception as e:
        logger.error(f"agent error: {e}")
        feishu.reply_message(msg.message_id, "系统处理异常，请稍后重试")


set_event_callback(P2ImMessageReceiveV1, on_message_received)


def main():
    logger.info("CommuFlow starting...")
    init_rag()
    config = Config(FEISHU_APP_ID, FEISHU_APP_SECRET)
    client = Client(config)
    logger.info("long connection starting...")
    client.event.start_loop()
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()