import sys, io; sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from utils.feishu_client import feishu

print("=== 1. Get Token ===")
token = feishu._get_token()
print(f"Token: {token[:20]}...")

print("\n=== 2. Test User Search ===")
users = feishu.search_user_by_name("")
print(f"Can query users: OK")