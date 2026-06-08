"""Task dashboard"""
from flask import Flask, render_template_string
from utils.task_manager import get_all_tasks

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head><title>CommuFlow Task Board</title>
<style>
body{font-family:Arial;margin:20px;background:#f5f5f5}
h1{color:#333}
table{border-collapse:collapse;width:100%;background:#fff}
th,td{border:1px solid #ddd;padding:10px;text-align:left}
th{background:#4a90d9;color:#fff}
tr:hover{background:#f0f0f0}
.pending{color:#f5a623}
.in_progress{color:#4a90d9}
.verify{color:#7b68ee}
.completed{color:#7ed321}
</style></head>
<body>
<h1>CommuFlow Task Board</h1>
<table>
<tr><th>ID</th><th>Title</th><th>Assignee</th><th>Due Date</th><th>Status</th></tr>
{% for t in tasks %}
<tr>
<td>T{{ t.id }}</td>
<td>{{ t.title }}</td>
<td>{{ t.assignee_name or t.assignee_openid[:12] }}</td>
<td>{{ t.due_date }}</td>
<td class="{{ t.status }}">{{ t.status }}</td>
</tr>
{% endfor %}
</table>
<p>[{{ tasks|length }} tasks]</p>
</body></html>
"""

@app.route("/")
def index():
    tasks = get_all_tasks()
    return render_template_string(HTML, tasks=tasks)

if __name__ == "__main__":
    from utils.task_manager import init_db
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)