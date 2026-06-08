import os
from dotenv import load_dotenv

load_dotenv()

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-v4-flash")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "commuflow.db")
VECTOR_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "vector_store")
KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), "..", "knowledge")