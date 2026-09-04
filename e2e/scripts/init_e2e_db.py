# -*- coding: utf-8 -*-
"""E2E 数据库初始化：创建独立 inkstone_e2e（不碰开发库），建 schema + 少量示例内容。

用法：python e2e/scripts/init_e2e_db.py
幂等：会 DROP 后重建 inkstone_e2e。
"""
import io
import os
import re
import pymysql

DB_NAME = "inkstone_e2e"
HOST, USER, PWD = "localhost", "root", "123456"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMA = os.path.join(ROOT, "server", "database", "schema.sql")

conn_kw = dict(host=HOST, user=USER, password=PWD, port=3306, autocommit=True, connect_timeout=10)

conn = pymysql.connect(**conn_kw)
with conn.cursor() as cur:
    cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    cur.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
conn.close()

with io.open(SCHEMA, "r", encoding="utf-8") as f:
    sql = f.read()
sql = re.sub(r"(?im)^CREATE DATABASE[^;]*;\s*", "", sql)
sql = re.sub(r"(?im)^USE [^;]*;\s*", "", sql)

conn = pymysql.connect(database=DB_NAME, client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS, **conn_kw)
with conn.cursor() as cur:
    cur.execute(sql)
    cur.execute("SELECT 1")  # 排空多语句
conn.close()

# 示例内容：少量诗词与素材（灵感馆/写作引用需要）
POEMS = [
    ("静夜思", "唐", "李白", "床前明月光，疑是地上霜。\n举头望明月，低头思故乡。", "思乡"),
    ("春晓", "唐", "孟浩然", "春眠不觉晓，处处闻啼鸟。\n夜来风雨声，花落知多少。", "写景"),
    ("江雪", "唐", "柳宗元", "千山鸟飞绝，万径人踪灭。\n孤舟蓑笠翁，独钓寒江雪。", "写景"),
    ("山行", "唐", "杜牧", "远上寒山石径斜，白云生处有人家。\n停车坐爱枫林晚，霜叶红于二月花。", "写景"),
]
MATERIALS = [
    ("雨夜", "雨打芭蕉，声声入耳。", "景物描写"),
    ("月色", "月光洒在石板路上，像铺了一层银霜。", "景物描写"),
    ("孤勇", "真正的勇敢，是明知会输依然前行。", "名言金句"),
    ("时间", "时间不是药，但药在时间里。", "名言金句"),
    ("重逢", "山高水远，总有人为你而来。", "情感表达"),
]
conn = pymysql.connect(database=DB_NAME, **conn_kw)
with conn.cursor() as cur:
    for title, dynasty, author, content, cat in POEMS:
        cur.execute(
            "INSERT INTO poems (title, dynasty, author, content, category) VALUES (%s,%s,%s,%s,%s)",
            (title, dynasty, author, content, cat),
        )
    for title, content, cat in MATERIALS:
        cur.execute(
            "INSERT INTO materials (title, content, category, source) VALUES (%s,%s,%s,'seed')",
            (title, content, cat),
        )
conn.commit()
conn.close()
print(f"init {DB_NAME} ok: poems={len(POEMS)} materials={len(MATERIALS)}")
