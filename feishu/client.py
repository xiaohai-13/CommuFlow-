import json
import requests
import lark_oapi as lark
from lark_oapi.api.im.v1 import *

from config import FEISHU_APP_ID, FEISHU_APP_SECRET


class FeishuClient:
    def __init__(self):
        self.app_id = FEISHU_APP_ID
        self.app_secret = FEISHU_APP_SECRET
        self._tenant_token = None

    def _get_token(self) -> str:
        if self._tenant_token:
            return self._tenant_token
        resp = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret}
        )
        data = resp.json()
        self._tenant_token = data.get("tenant_access_token", "")
        return self._tenant_token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json"
        }

    def get_user_info(self, open_id: str) -> dict:
        resp = requests.get(
            f"https://open.feishu.cn/open-apis/contact/v3/users/{open_id}",
            headers=self._headers()
        )
        data = resp.json()
        user = data.get("data", {}).get("user", {})
        return {"name": user.get("name", ""), "open_id": open_id}

    def search_user_by_name(self, name: str) -> dict | None:
        resp = requests.get(
            "https://open.feishu.cn/open-apis/contact/v3/users",
            headers=self._headers(),
            params={"page_size": 20}
        )
        data = resp.json()
        items = data.get("data", {}).get("items", [])
        for u in items:
            if name in u.get("name", ""):
                return {"name": u["name"], "open_id": u["open_id"]}
        return None

    def get_message_content(self, message_id: str) -> str:
        resp = requests.get(
            f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}",
            headers=self._headers()
        )
        data = resp.json()
        items = data.get("data", {}).get("items", [])
        for item in items:
            if item.get("msg_type") == "text":
                return json.loads(item.get("body", "{}").get("content", "{}")).get("text", "")
        return ""

    def send_text(self, chat_id: str, text: str):
        content = json.dumps({"text": text})
        payload = {
            "receive_id": chat_id,
            "msg_type": "text",
            "content": content
        }
        requests.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            headers=self._headers(),
            params={"receive_id_type": "chat_id"},
            json=payload
        )

    def reply_message(self, message_id: str, text: str):
        content = json.dumps({"text": text})
        payload = {
            "msg_type": "text",
            "content": content
        }
        requests.post(
            f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply",
            headers=self._headers(),
            json=payload
        )

    def at_user(self, open_id: str) -> str:
        return f"<at user_id=\"{open_id}\"></at>"


feishu = FeishuClient()
