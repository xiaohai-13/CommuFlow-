import json
import requests
from utils.config import FEISHU_APP_ID, FEISHU_APP_SECRET
from utils.logger import logger


class FeishuClient:
    def __init__(self):
        self.app_id = FEISHU_APP_ID
        self.app_secret = FEISHU_APP_SECRET
        self._token = None

    def _get_token(self) -> str:
        if self._token:
            return self._token
        resp = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret}
        )
        data = resp.json()
        self._token = data.get("tenant_access_token", "")
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._get_token()}", "Content-Type": "application/json"}

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
            params={"page_size": 50}
        )
        data = resp.json()
        items = data.get("data", {}).get("items", [])
        for u in items:
            if name in u.get("name", ""):
                return {"name": u["name"], "open_id": u["open_id"]}
        return None

    def send_text(self, receive_id: str, content: str, receive_type: str = "open_id"):
        payload = {
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": content})
        }
        resp = requests.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            headers=self._headers(),
            params={"receive_id_type": receive_type},
            json=payload
        )
        if not resp.json().get("code") == 0:
            logger.error(f"send_text failed: {resp.json()}")

    def reply_message(self, message_id: str, content: str):
        payload = {
            "msg_type": "text",
            "content": json.dumps({"text": content})
        }
        resp = requests.post(
            f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply",
            headers=self._headers(),
            json=payload
        )
        if not resp.json().get("code") == 0:
            logger.error(f"reply failed: {resp.json()}")

    def at_user(self, open_id: str) -> str:
        return f"<at user_id=\"{open_id}\"></at>"

    def create_task(self, summary: str, due_time: str = "", assignee_id: str = ""):
        body = {"summary": summary, "due_time": due_time}
        if assignee_id:
            body["assignee_id"] = assignee_id
        resp = requests.post(
            "https://open.feishu.cn/open-apis/task/v1/tasks",
            headers=self._headers(),
            json=body
        )
        return resp.json()


feishu = FeishuClient()