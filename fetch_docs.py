import urllib.request, re
url = "https://open.feishu.cn/document/server-docs/im-v1/message-content-description/message_content"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
resp = urllib.request.urlopen(req, timeout=10)
html = resp.read().decode("utf-8")

# Extract code blocks and JSON examples
blocks = re.findall(r'<code[^>]*>(.*?)</code>', html, re.DOTALL)
for b in blocks:
    if "text" in b and "mentions" in b:
        print(b[:500])
        print("===")