import sys; sys.path.insert(0, '.')
import io; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import json, re
from config import OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

text = '请@李芳 在6月15日前完成市场调研，包含竞品分析'
prompt = 'Extract task info from message as JSON with fields: title, assignee, due_date, description, dependency. If missing use empty string. Message: ' + text + '
Return ONLY valid JSON.'

resp = client.chat.completions.create(model=LLM_MODEL, messages=[{'role':'user','content':prompt}], temperature=0, max_tokens=300)
content = resp.choices[0].message.content
print('RAW:', repr(content))