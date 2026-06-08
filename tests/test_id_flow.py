# -*- coding: utf-8 -*-
import sys, io, re
sys.path.insert(0, '.')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from agent.graph import run_agent
from agent.memory import clear_history
from utils.task_manager import init_db, get_all_tasks

init_db()
clear_history('t1')
CREATOR = 'ou_creator'
ASSIGNEE = 'ou_assignee'
MENTIONS = {'@_user_2': {'name': 'userB', 'open_id': ASSIGNEE}}

def sim(text, sender, mm=None):
    return run_agent(user_id=sender, chat_id='t1', text=text, mention_map=mm or {})

print('=== CREATE ===')
r = sim('qing @userB next Friday 18:00 finish market analysis', CREATOR, MENTIONS)
print(r[:200])
tid = re.search(r'T\d{3}', r)
assert tid, 'No task ID in reply!'
task_id = tid.group()
print('Task ID: ' + task_id)

print('\n=== QUERY ===')
r = sim('my tasks', ASSIGNEE)
print(r[:200])
assert task_id in r, 'Task not visible'

print('\n=== COMPLETE ===')
r = sim(task_id + ' done', ASSIGNEE)
print(r[:200])

print('\n=== VERIFY ===')
r = sim(task_id + ' accept', CREATOR)
print(r[:200])

print('\n=== FINAL DB ===')
for t in get_all_tasks():
    tid2 = str(t['id'])
    ts = t['status']
    tt = t['title']
    ta = t['assignee_openid']
    print('  T' + tid2 + ' [' + ts + '] ' + tt + ' -> ' + ta)

print('\nALL PASSED')
