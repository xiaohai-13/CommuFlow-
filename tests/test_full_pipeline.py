"""
================================================================================
  CommuFlow 全流程综合测试
  模拟飞书消息 JSON 格式 → 走完整 LangGraph pipeline
  覆盖：单人/双人/多人编排 + 知识库 + 会议纪要 + 看板
================================================================================
用法: python tests/test_full_pipeline.py
"""
import sys, io, json, re
sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from agent.graph import run_agent
from agent.memory import clear_history, load_history
from utils.task_manager import init_db, get_all_tasks
from utils.logger import logger

init_db()

# ═══════════════════════════════════════════════════
# 模拟用户身份（对应飞书 open_id）
# ═══════════════════════════════════════════════════
小海 = "ou_xiaohai"        # 项目经理
张三 = "ou_zhangsan"       # 开发
李四 = "ou_lisi"           # 设计
王五 = "ou_wangwu"         # 测试

# 飞书 mentions 格式（模拟真实事件中的 JSON）
def make_mentions(*users):
    """构造飞书 mentions 列表。users: [(name, open_id), ...]"""
    result = {}
    for i, (name, oid) in enumerate(users, 1):
        key = f"@_user_{i}"
        result[key] = {"name": name, "open_id": oid}
    return result

def feishu_msg(sender, text, mentions=None):
    """模拟飞书收到一条消息，返回 Agent 回复"""
    # 替换 @_user_X → @用户名（模拟 main.py 的预处理）
    clean = text
    if mentions:
        for key, info in mentions.items():
            clean = clean.replace(key, f"@{info['name']}")
    return run_agent(sender, "oc_test_group", clean, mentions or {})

# ═══════════════════════════════════════════════════
# 清理旧数据
# ═══════════════════════════════════════════════════
import sqlite3, os
for db in ["data/commuflow.db", "data/memory.db"]:
    if os.path.exists(db):
        c = sqlite3.connect(db)
        c.execute("DELETE FROM tasks" if "commuflow" in db else "DELETE FROM conversations")
        c.commit()
        c.close()
clear_history("oc_test_group")
init_db()
logger.info("=== TEST DATA CLEARED ===")

print("=" * 70)
print("  CommuFlow 全流程测试")
print("  模拟飞书消息 JSON 格式，走完整 LangGraph pipeline")
print("=" * 70)

# ═══════════════════════════════════════════════════
# 场景 1: 单人任务闭环
# ═══════════════════════════════════════════════════
print("\n" + "─" * 70)
print("  场景 1: 单人任务闭环（小海 → 张三 → 小海验收）")
print("─" * 70)

m = make_mentions(("张三", 张三))

# 1a: 创建任务
print("\n[1a] 小海: @CommuFlow 请@张三 下周五18:00前完成竞品分析报告")
r = feishu_msg(小海, "@_user_1 请@_user_1 下周五18:00前完成竞品分析报告", m)
print(f"      CommuFlow: {r}")

# 提取 T00X
tid_match = re.search(r"T\d{3}", r)
task1_id = tid_match.group() if tid_match else "???"
print(f"      → 任务ID: {task1_id}")

# 1b: 张三查任务
print(f"\n[1b] 张三: @CommuFlow 我的任务有哪些")
r = feishu_msg(张三, "我的任务有哪些")
print(f"      CommuFlow: {r}")

# 1c: 张三完成任务
print(f"\n[1c] 张三: @CommuFlow {task1_id} 已完成")
r = feishu_msg(张三, f"{task1_id} 已完成")
print(f"      CommuFlow: {r}")

# 1d: 小海验收
print(f"\n[1d] 小海: @CommuFlow {task1_id} 验收通过")
r = feishu_msg(小海, f"{task1_id} 验收通过")
print(f"      CommuFlow: {r}")

# ═══════════════════════════════════════════════════
# 场景 2: 多人编排（一人分配多任务）
# ═══════════════════════════════════════════════════
print("\n" + "─" * 70)
print("  场景 2: 多人编排（小海同时给张三、李四分任务）")
print("─" * 70)

m2 = make_mentions(("张三", 张三), ("李四", 李四))

# 2a: 给张三派活
print("\n[2a] 小海: @CommuFlow 请@张三 2026-06-20前完成后端API开发")
r = feishu_msg(小海, "@_user_1 请@_user_1 2026-06-20前完成后端API开发", m2)
print(f"      CommuFlow: {r}")
tid2 = re.search(r"T\d{3}", r).group() if re.search(r"T\d{3}", r) else "???"

# 2b: 给李四派活
print("\n[2b] 小海: @CommuFlow 请@李四 2026-06-18前完成UI设计稿")
r = feishu_msg(小海, "@_user_2 请@_user_2 2026-06-18前完成UI设计稿", m2)
print(f"      CommuFlow: {r}")
tid3 = re.search(r"T\d{3}", r).group() if re.search(r"T\d{3}", r) else "???"

print(f"\n      → 创建了 {tid2} 和 {tid3}")

# 2c: 张三查自己的任务
print(f"\n[2c] 张三: @CommuFlow 我的任务有哪些")
r = feishu_msg(张三, "我的任务有哪些")
print(f"      CommuFlow: {r}")

# 2d: 李四查自己的任务
print(f"\n[2d] 李四: @CommuFlow 我的任务有哪些")
r = feishu_msg(李四, "我的任务有哪些")
print(f"      CommuFlow: {r}")

# 2e: 张三完成任务
print(f"\n[2e] 张三: @CommuFlow 后端API开发 已完成")
r = feishu_msg(张三, "后端API开发 已完成")
print(f"      CommuFlow: {r}")

# 2f: 李四完成任务
print(f"\n[2f] 李四: @CommuFlow UI设计稿 已完成")
r = feishu_msg(李四, "UI设计稿 已完成")
print(f"      CommuFlow: {r}")

# 2g: 小海逐个验收
print(f"\n[2g] 小海: @CommuFlow {tid2} 验收通过")
r = feishu_msg(小海, f"{tid2} 验收通过")
print(f"      CommuFlow: {r}")

print(f"\n[2h] 小海: @CommuFlow 验收通过  (自动匹配下一个)")
r = feishu_msg(小海, "验收通过")
print(f"      CommuFlow: {r}")

# ═══════════════════════════════════════════════════
# 场景 3: 知识问答
# ═══════════════════════════════════════════════════
print("\n" + "─" * 70)
print("  场景 3: 知识库问答（RAG）")
print("─" * 70)

print("\n[3a] 小海: @CommuFlow 紧急订单变更流程是什么？")
r = feishu_msg(小海, "紧急订单变更流程是什么？")
print(f"      CommuFlow: {r}")

print("\n[3b] 小海: @CommuFlow 采购标准交期是多久？")
r = feishu_msg(小海, "采购标准交期是多久？")
print(f"      CommuFlow: {r}")

# ═══════════════════════════════════════════════════
# 场景 4: 会议纪要
# ═══════════════════════════════════════════════════
print("\n" + "─" * 70)
print("  场景 4: 会议纪要生成")
print("─" * 70)

meeting_text = """会议记录：
今天下午2点我们开了Q2产品评审会。参会人员：小海、张三、李四、王五。
讨论了三个议题：1) 竞品分析报告需要增加市场数据对比；2) 后端API需要支持批量导入；
3) UI设计稿配色需要调整为企业蓝色系。
结论：竞品报告由张三6月20日前补充数据，后端API由张三6月25日前开发完成，
UI配色由李四6月15日前调整。测试由王五负责6月30日完成集成测试。"""

print(f"\n[4a] 小海: @CommuFlow 帮我整理会议纪要：\n{meeting_text[:60]}...")
r = feishu_msg(小海, f"帮我整理会议纪要：\n{meeting_text}")
print(f"      CommuFlow:\n{r}")

# ═══════════════════════════════════════════════════
# 场景 5: 聊天兜底
# ═══════════════════════════════════════════════════
print("\n" + "─" * 70)
print("  场景 5: 闲聊兜底")
print("─" * 70)

print("\n[5a] 用户: @CommuFlow 你好")
r = feishu_msg(小海, "你好")
print(f"      CommuFlow: {r}")

# ═══════════════════════════════════════════════════
# 看板输出
# ═══════════════════════════════════════════════════
print("\n" + "=" * 70)
print("  最终任务看板")
print("=" * 70)

print(f"\n{'ID':<6} {'Status':<12} {'Title':<20} {'Assignee':<15} {'Due Date'}")
print("-" * 70)
for t in get_all_tasks():
    status_map = {"pending":"待处理","verified":"待验收","completed":"已完成","in_progress":"进行中"}
    st = status_map.get(t["status"], t["status"])
    print(f"T{t['id']:<04d} {st:<12} {t['title']:<20} {t['assignee_openid'][:15]:<15} {t['due_date']}")

print(f"\n共 {len(get_all_tasks())} 个任务")
print("=" * 70)
print("  全流程测试完成！")
print("=" * 70)
