import sys; sys.path.insert(0, '.')
import io; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from config import OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

resp = client.chat.completions.create(
    model=LLM_MODEL,
    messages=[{"role":"user","content":"say hello"}],
    temperature=0, max_tokens=100
)
print("MODEL:", LLM_MODEL)
print("CONTENT:", repr(resp.choices[0].message.content))
print("FINISH:", resp.choices[0].finish_reason)