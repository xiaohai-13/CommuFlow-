import sys; sys.path.insert(0, '.')
import io; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import json, re
from config import OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

text = 'qing @lifang zai 6yue15ri qian wancheng shichang diaoyan'
prompt = f'Extract task info from: {text}\nReturn ONLY valid JSON: {{"title":"...","assignee":"...","due_date":"...","description":"...","dependency":"..."}}'

resp = client.chat.completions.create(
    model=LLM_MODEL,
    messages=[{'role':'user','content':prompt}],
    temperature=0, max_tokens=300
)
content = resp.choices[0].message.content.strip()
print("RAW REPLY:", repr(content))
try:
    content = re.sub(r'^.*?(\{.*\}).*$', r'\1', content, flags=re.DOTALL)
    print("CLEANED:", repr(content))
    result = json.loads(content)
    print("PARSED:", result)
except Exception as e:
    print("PARSE ERROR:", e)