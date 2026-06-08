from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from db.models import query_overdue_tasks
from feishu.client import feishu

scheduler = BackgroundScheduler()


def check_overdue():
    tasks = query_overdue_tasks()
    for task in tasks:
        msg = (
            f"⏰ 催办提醒\n"
            f"任务 {task['id']}「{task['title']}」已逾期！\n"
            f"截止时间：{task['due_date']}\n"
            f"{feishu.at_user(task['assignee_openid'])} 请尽快处理。"
        )
        print(f"[催办] {task['id']} -> {task['assignee_name']}")


def start_scheduler():
    scheduler.add_job(check_overdue, 'interval', hours=4, id='overdue_check')
    scheduler.start()
    print("催办定时任务已启动（每4小时）")
