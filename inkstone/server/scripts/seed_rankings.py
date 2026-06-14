"""排行榜补充种子数据 — 新增用户、作品、互动数据。"""

from database.db import query, execute
import bcrypt
import random
from datetime import date, timedelta

random.seed(99)


def seed_extra_users():
    """Add more users for richer rankings."""
    existing = query('SELECT COUNT(*) as cnt FROM users')[0]['cnt']
    if existing >= 19:
        print(f'Extra users already seeded ({existing} users).')
        return

    pw = bcrypt.hashpw('123456'.encode(), bcrypt.gensalt()).decode()
    users = [
        ('鲁迅', '以笔为刀，以文为剑', 7, 35000),
        ('金庸', '飞雪连天射白鹿', 8, 85000),
        ('莫言', '高密东北乡的故事', 5, 9500),
        ('三毛', '撒哈拉的流浪者', 6, 18000),
        ('余华', '活着就是一切', 4, 5500),
        ('王小波', '沉默的大多数', 5, 12000),
        ('迟子建', '北极村的故事', 3, 2800),
        ('苏童', '妻妾成群的作者', 4, 6200),
        ('刘亮程', '一个人的村庄', 3, 3100),
        ('阿来', '尘埃落定的书写者', 4, 7800),
    ]
    count = 0
    for name, bio, level, exp in users:
        execute(
            'INSERT INTO users (username, password_hash, bio, level, exp) VALUES (%s, %s, %s, %s, %s)',
            (name, pw, bio, level, exp)
        )
        count += 1
    print(f'Seeded {count} extra users.')


def seed_extra_works():
    """Add more published works with varied stats."""
    users = query('SELECT user_id, username FROM users ORDER BY user_id')
    if len(users) < 10:
        print('Not enough users for extra works.')
        return

    # Check if extra works already seeded
    cnt = query("SELECT COUNT(*) as c FROM works WHERE title LIKE '【榜】%'")[0]['c']
    if cnt > 0:
        print(f'Extra works already seeded ({cnt} works).')
        return

    extra_works = [
        # 鲁迅 (user_id index 9)
        (users[9]['user_id'], '【榜】朝花夕拾新编', 'essay', '从百草园到三味书屋，童年的记忆在文字中重新鲜活。', '散文,回忆,童年', 'published', 3200, 156, 42, 28),
        (users[9]['user_id'], '【榜】呐喊之后', 'novel', '狂人日记的续篇。那个看透了吃人社会的狂人，后来怎样了？', '小说,讽刺,社会', 'published', 8500, 234, 67, 45),
        # 金庸 (user_id index 10)
        (users[10]['user_id'], '【榜】天龙八部后传', 'novel', '乔峰死后三十年，段誉之子与虚竹之徒联手对抗一个新的江湖势力。', '武侠,江湖,英雄', 'published', 15600, 523, 134, 89),
        (users[10]['user_id'], '【榜】笑傲江湖前传', 'novel', '华山派剑气之争的真相。风清扬年轻时的故事，以及独孤九剑的由来。', '武侠,华山,剑法', 'published', 12000, 387, 98, 67),
        # 莫言 (user_id index 11)
        (users[11]['user_id'], '【榜】高密往事', 'novel', '高密东北乡的百年沧桑。从清末到新世纪，一个村庄的史诗。', '乡土,历史,魔幻', 'published', 9800, 178, 45, 32),
        # 三毛 (user_id index 12)
        (users[12]['user_id'], '【榜】撒哈拉的故事续', 'essay', '三毛在撒哈拉的第二年。荷西的潜水事故、沙漠中的邻居们、以及那些永远不会忘记的日落。', '散文,旅行,爱情', 'published', 6500, 412, 112, 78),
        (users[12]['user_id'], '【榜】万水千山走遍', 'essay', '从南美到欧洲，从非洲到亚洲。三毛的旅行随笔，记录那些在路上遇见的人和事。', '旅行,随笔,人生', 'published', 5200, 298, 76, 54),
        # 余华 (user_id index 13)
        (users[13]['user_id'], '【榜】活着之后', 'novel', '福贵老了。他坐在村口的石头上，看着来来往往的年轻人，想起了那些已经离开的人。', '小说,人生,苦难', 'published', 7800, 345, 89, 61),
        # 王小波 (user_id index 14)
        (users[14]['user_id'], '【榜】沉默的大多数续', 'essay', '关于自由、理性与有趣。王小波未发表的杂文集。', '杂文,自由,理性', 'published', 4500, 267, 68, 47),
        (users[14]['user_id'], '【榜】黄金时代后传', 'novel', '王二在云南的第二年。破鞋的故事还在继续，但这一次他遇到了一个不一样的人。', '小说,幽默,知青', 'published', 6200, 198, 52, 38),
        # 迟子建 (user_id index 15)
        (users[15]['user_id'], '【榜】北极村的冬天', 'novel', '漠河的冬天零下四十度。一个女孩在冰天雪地中长大，她的故事像北方的白桦林一样坚韧。', '北方,成长,自然', 'published', 4800, 156, 38, 25),
        # 苏童 (user_id index 16)
        (users[16]['user_id'], '【榜】妻妾成群新解', 'novel', '用现代视角重读旧时代的故事。颂莲的悲剧，不只是一个女人的悲剧。', '小说,女性,旧时代', 'published', 5600, 189, 47, 33),
        # 刘亮程 (user_id index 17)
        (users[17]['user_id'], '【榜】一个人的村庄续', 'essay', '刘亮程回到黄沙梁。二十年过去了，村庄变了，但他记忆中的那棵树还在。', '散文,村庄,记忆', 'published', 3200, 134, 32, 21),
        # 阿来 (user_id index 18)
        (users[18]['user_id'], '【榜】尘埃落定之后', 'novel', '土司制度消亡后的康巴高原。新的秩序在废墟上建立，但旧的灵魂仍在游荡。', '小说,藏族,历史', 'published', 7200, 167, 43, 29),
    ]

    count = 0
    for uid, title, typ, summary, tags, status, wc, views, likes, comments in extra_works:
        execute(
            'INSERT INTO works (user_id, title, type, summary, tags, status, word_count, views, likes_count, comments_count) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            [uid, title, typ, summary, tags, status, wc, views, likes, comments]
        )
        count += 1
    print(f'Seeded {count} extra works.')


def seed_extra_interactions():
    """Add likes, comments, favorites for the new works."""
    works = query("SELECT work_id FROM works WHERE title LIKE '【榜】%'")
    users = query('SELECT user_id FROM users')
    if not works or not users:
        print('No extra works/users found, skipping interactions.')
        return

    # Check if already seeded
    cnt = query("SELECT COUNT(*) as c FROM comments WHERE content LIKE '%【热评】%'")[0]['c']
    if cnt > 0:
        print(f'Extra interactions already seeded.')
        return

    work_ids = [w['work_id'] for w in works]
    user_ids = [u['user_id'] for u in users]

    # Add random likes
    like_count = 0
    for wid in work_ids:
        likers = random.sample(user_ids, min(len(user_ids), random.randint(3, 8)))
        for uid in likers:
            try:
                execute('INSERT IGNORE INTO work_likes (user_id, work_id) VALUES (%s, %s)', [uid, wid])
                like_count += 1
            except:
                pass
    print(f'Seeded {like_count} extra likes.')

    # Add random favorites
    fav_count = 0
    for wid in work_ids:
        favers = random.sample(user_ids, min(len(user_ids), random.randint(2, 5)))
        for uid in favers:
            try:
                execute('INSERT IGNORE INTO favorites (user_id, work_id) VALUES (%s, %s)', [uid, wid])
                fav_count += 1
            except:
                pass
    print(f'Seeded {fav_count} extra favorites.')

    # Add comments
    comment_templates = [
        '【热评】写得太好了，一口气读完！',
        '【热评】文笔细腻，情感真挚，推荐！',
        '【热评】这个故事让我想起了自己的经历。',
        '【热评】期待后续更新！',
        '【热评】人物塑造很立体，有血有肉。',
        '【热评】情节跌宕起伏，看得停不下来。',
        '【热评】作者的文风很有辨识度。',
        '【热评】这个结局出乎意料又在情理之中。',
        '【热评】每一段都值得细细品味。',
        '【热评】读完之后久久不能平静。',
    ]
    comment_count = 0
    for wid in work_ids:
        commenters = random.sample(user_ids, min(len(user_ids), random.randint(2, 6)))
        for uid in commenters:
            content = random.choice(comment_templates)
            try:
                execute(
                    'INSERT INTO comments (work_id, user_id, content) VALUES (%s, %s, %s)',
                    [wid, uid, content]
                )
                comment_count += 1
            except:
                pass
    print(f'Seeded {comment_count} extra comments.')

    # Add follows (follow popular authors)
    popular_users = [u['user_id'] for u in query('SELECT user_id FROM users ORDER BY exp DESC LIMIT 5')]
    follow_count = 0
    for uid in user_ids:
        targets = random.sample([u for u in popular_users if u != uid], min(3, len(popular_users) - 1))
        for target in targets:
            try:
                execute('INSERT IGNORE INTO follows (follower_id, following_id) VALUES (%s, %s)', [uid, target])
                follow_count += 1
            except:
                pass
    print(f'Seeded {follow_count} extra follows.')


def seed_extra_chapters():
    """Add chapters for new works."""
    works = query("SELECT work_id, title FROM works WHERE title LIKE '【榜】%' AND work_id NOT IN (SELECT DISTINCT work_id FROM chapters)")
    if not works:
        print('No extra works need chapters.')
        return

    chapter_templates = [
        ('第一章', '这是一个关于勇气与选择的故事。开篇以一个平凡的场景切入，却在字里行间埋下了不平凡的伏笔。'),
        ('第二章', '故事渐入佳境。人物之间的关系开始变得复杂，每一个决定都牵动着后续的发展。'),
        ('第三章', '高潮来临。所有的铺垫在这一刻爆发，读者的情绪也随之到达顶点。'),
    ]

    count = 0
    for w in works:
        for i, (ch_title, ch_content) in enumerate(chapter_templates):
            execute(
                'INSERT INTO chapters (work_id, chapter_no, title, content, word_count) VALUES (%s, %s, %s, %s, %s)',
                [w['work_id'], i + 1, ch_title, ch_content, len(ch_content)]
            )
            count += 1
    print(f'Seeded {count} extra chapters.')


if __name__ == '__main__':
    print('Seeding extra ranking data...')
    seed_extra_users()
    seed_extra_works()
    seed_extra_chapters()
    seed_extra_interactions()
    print('Done!')
