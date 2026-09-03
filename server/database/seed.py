"""Seed data for Inkstone — comprehensive sample data for testing."""

from database.db import query, execute
import bcrypt
from datetime import date, timedelta
import random

random.seed(42)


def _exists(table):
    """Check if a table has any rows. Table name is always hardcoded internally."""
    return query(f'SELECT COUNT(*) as cnt FROM `{table}`')[0]['cnt'] > 0


def seed_achievements():
    if _exists('achievements'):
        print(f'Achievements already seeded.')
        return

    achievements = [
        # 写作成就
        ('初试啼声', '发布第一篇作品', '📝', 'works', 1),
        ('笔耕不辍', '累计写作1万字', '✍️', 'word_count', 10000),
        ('著作等身', '累计写作10万字', '📚', 'word_count', 100000),
        ('万众瞩目', '作品累计获得100个赞', '❤️', 'likes', 100),
        ('话题之王', '作品累计收到50条评论', '💬', 'comments', 50),
        ('高产作家', '发布10篇作品', '🏆', 'works', 10),
        ('每日打卡7天', '连续打卡7天', '🔥', 'checkin_days', 7),
        ('每日打卡30天', '连续打卡30天', '💎', 'checkin_days', 30),
        ('初具人望', '收获10个粉丝', '👥', 'followers', 10),
        ('声名远播', '收获100个粉丝', '🌟', 'followers', 100),
        # 阅读成就
        ('初识书香', '读完第1本书', '📖', 'books_read', 1),
        ('博览群书', '读完10本书', '📗', 'books_read', 10),
        ('学富五车', '读完50本书', '🏛️', 'books_read', 50),
        ('日拱一卒', '连续阅读打卡7天', '📅', 'reading_streak', 7),
        ('锲而不舍', '连续阅读打卡30天', '🗓️', 'reading_streak', 30),
        ('书山有路', '累计阅读100小时', '⏰', 'reading_hours', 100),
        ('笔墨生香', '写下100条批注', '🖊️', 'annotations', 100),
        ('字字珠玑', '标记50条好句', '✨', 'highlights', 50),
    ]
    for name, desc, icon, ctype, cval in achievements:
        execute(
            'INSERT INTO achievements (name, description, icon, condition_type, condition_value) VALUES (%s, %s, %s, %s, %s)',
            (name, desc, icon, ctype, cval)
        )
    print(f'Seeded {len(achievements)} achievements.')


def seed_users():
    if _exists('users'):
        print('Users already seeded.')
        return

    users = [
        ('李白', '诗人李白，热爱古风创作', 5, 8000),
        ('村上春树', '写小说的调酒师', 4, 4500),
        ('张爱玲', '散文与小说的边缘', 6, 15000),
        ('刘慈欣', '科幻世界建造者', 3, 2200),
        ('JK罗琳', '魔法故事的编织者', 4, 5000),
    ]
    pw = bcrypt.hashpw('123456'.encode(), bcrypt.gensalt()).decode()
    for name, bio, level, exp in users:
        execute(
            'INSERT INTO users (username, password_hash, bio, level, exp) VALUES (%s, %s, %s, %s, %s)',
            (name, pw, bio, level, exp)
        )
    print(f'Seeded {len(users)} users (password: 123456).')


def seed_works():
    if _exists('works'):
        print('Works already seeded.')
        return

    user_ids = [r['user_id'] for r in query('SELECT user_id FROM users')]
    if not user_ids:
        print('No users found, skipping works.')
        return

    works_data = [
        # user 1 — 李白
        (user_ids[0], '月下独酌集', 'poetry', '举杯邀明月，对影成三人。收录三十首古风诗词，涵盖山水、饮酒、怀古诸题。', '古风,诗词,山水', 'published'),
        (user_ids[0], '长安十二时辰', 'novel', '天宝三载，上元节前夕，长安城陷入了一场惊天阴谋。一名死囚与一位少年名士联手，在十二时辰内拯救这座伟大的城市。', '古风,悬疑,历史', 'published'),
        (user_ids[0], '蜀道行', 'poetry', '噫吁嚱，危乎高哉！蜀道之难，难于上青天！长篇古风叙事诗，描绘蜀道壮丽与艰险。', '古风,山水,叙事', 'draft'),
        # user 2 — 村上春树
        (user_ids[1], '挪威的森林续', 'novel', '多年后的重逢。直子离开后的第三年，渡边在东京的爵士酒吧里再次听到了那首 Norwegian Wood。这一次，他决定不再逃避。', '青春,爱情,都市', 'published'),
        (user_ids[1], '爵士酒吧物语', 'essay', '深夜的爵士酒吧，威士忌与黑胶唱片。记录那些在音乐中相遇又分离的人们。', '都市,随笔,音乐', 'published'),
        (user_ids[1], '跑步与写作', 'essay', '从神宫外苑到查尔斯河畔，二十五年跑步生涯的思考碎片。', '随笔,运动,人生', 'published'),
        # user 3 — 张爱玲
        (user_ids[2], '倾城之恋补遗', 'novel', '白流苏与范柳原的故事，还有一个不为人知的版本。旧上海的旗袍、留声机与电车铃声中，藏着另一个结局。', '爱情,民国,都市', 'published'),
        (user_ids[2], '流言集', 'essay', '生活是一袭华美的袍，爬满了蚤子。短篇散文集，关于吃食、衣着、街景与人事。', '散文,生活,民国', 'published'),
        (user_ids[2], '红玫瑰与白玫瑰', 'poetry', '也许每一个男子全都有过这样的两个女人。诗剧体作品，以诗歌形式重新演绎经典故事。', '爱情,诗歌,经典', 'private'),
        # user 4 — 刘慈欣
        (user_ids[3], '三体：黑暗森林外传', 'script', '面壁计划之外，还有一位未被记录的面壁者。他的故事，将揭示黑暗森林法则的另一个维度。', '科幻,宇宙,文明', 'published'),
        (user_ids[3], '球状闪电考', 'novel', '一个关于球状闪电的科学猜想，以及对战争与和平的终极思考。', '科幻,军事,哲学', 'published'),
        (user_ids[3], '流浪地球纪事', 'script', '太阳即将毁灭，人类带着地球踏上两千五百年的流浪之旅。舞台剧本改编。', '科幻,灾难,剧本', 'draft'),
        # user 5 — JK罗琳
        (user_ids[4], '魔法部秘档', 'script', '在霍格沃茨之外，魔法部的公务员们也有自己的冒险。一部关于官僚、魔法与友情的情景喜剧剧本。', '奇幻,喜剧,魔法', 'published'),
        (user_ids[4], '霍格沃茨的秋天', 'novel', '霍格沃茨新学期开始了。一个来自麻瓜家庭的新生发现了一本古老的魔法日记，日记里记载着一个被遗忘的黑魔法秘密。', '奇幻,魔法,校园', 'published'),
        (user_ids[4], '创作手记', 'essay', '从咖啡馆里的涂鸦到全球畅销书，一个关于想象力如何变成文字的故事。关于写作、魔法与坚持的随笔集。', '随笔,创作,人生', 'published'),
    ]

    # Chapters for each work (work index in works_data → chapters)
    chapters_data = [
        [('自序', '余平生好酒，又好诗。每于月明之夜，独酌花间，兴之所至，辄成篇章。今辑三十首，以飨同好。诗者，心声也。或咏山水之壮丽，或叹人生之无常，或寄情于酒，或托意于月。诸君读之，若能会心一笑，则余愿足矣。'),
         ('卷一·山水篇', '飞流直下三千尺，疑是银河落九天。庐山之瀑，天下奇观也。余尝三往观之，每至则心魄震荡，不能自已。水声如雷，白练如虹，天地之间，唯此一派浩然之气。'),
         ('卷二·饮酒篇', '五花马，千金裘，呼儿将出换美酒，与尔同销万古愁。醉后不知天在水，满船清梦压星河。'),
         ('卷三·怀古篇', '大江东去，浪淘尽，千古风流人物。登金陵凤凰台，望长安不见，使人愁。古今多少事，都付笑谈中。')],
        [('第一章·死囚', '天宝三载，正月十四。长安城一百零八坊笼罩在冬日的薄雾中。大理寺的死牢里，张小敬睁开眼，听见了远处的爆竹声。上元节快到了。他本应在三日后问斩，但今天，一个意外的访客改变了一切。'),
         ('第二章·靖安司', '李必站在靖安司的沙盘前，长安城的微缩模型在烛光下静静卧着。二十四岁的少年名士，太子党的核心人物——他只有十二个时辰来阻止一场足以毁灭长安的阴谋。而他唯一的选择，是一个死囚。'),
         ('第三章·狼卫', '狼卫已潜入长安。他们是突厥的精锐，为复仇而来。张小敬循着线索穿过平康坊的烟花巷、西市的胡商摊位，每一步都踩在刀尖上。他发现这场阴谋的规模远超想象——有人想在长安城点燃一场大火。')],
        [('上篇·入蜀', '噫吁嚱，危乎高哉！蜀道之难，难于上青天！蚕丛及鱼凫，开国何茫然！尔来四万八千岁，不与秦塞通人烟。西当太白有鸟道，可以横绝峨眉巅。地崩山摧壮士死，然后天梯石栈相钩连。'),
         ('下篇·出蜀', '朝避猛虎，夕避长蛇。磨牙吮血，杀人如麻。锦城虽云乐，不如早还家。蜀道之难，难于上青天，侧身西望长咨嗟！归去来兮，田园将芜胡不归？'),],
        [('第一章·归来的渡边', '三十七岁的渡边坐在新宿的一家爵士酒吧里，听到了那段熟悉的旋律。Norwegian Wood。十三年了，他以为自己早已忘记，但音乐响起的那一刻，一切都回来了。'),
         ('第二章·阿美寮的来信', '一封没有署名的信寄到了渡边的公寓。信纸上只有一句话："我在阿美寮，等你。"邮戳是神户。渡边知道是谁——只有一个人会这样写信。'),
         ('第三章·再会', '阿美寮的疗养院依旧被森林包围。渡边在门口站了很久，阳光透过树叶的缝隙落在他的肩上。然后直子走了出来。她瘦了很多，但眼神不再空洞。他们相视一笑，像两个在黑暗中摸索多年终于找到出口的人。')],
        [('深夜的爵士酒吧', '这家酒吧藏在神宫外苑附近的一条小巷里，门外连招牌都没有。推开厚重的木门，威士忌和旧书的气味扑面而来。吧台后，老板正用留声机放着 Bill Evans 的《Waltz for Debby》。这里的客人都知道一个规矩：进了门，就别再谈外面的事。')],
        [('第一章·神宫外苑', '从神宫外苑到查尔斯河畔，二十五年。每天清晨五点起床，穿上跑鞋，推开门。不是为了比赛，不是为了健康——只是需要那段空白的时间，让思绪自由漂流。'), ('第二章·查尔斯河', '在波士顿的那几年，我住在查尔斯河附近。秋天的河面倒映着两岸的红叶，晨跑的人三三两两。有时候会想起村上春树——另一个在查尔斯河畔跑步的作家，只不过他已经离开了，而我刚刚到来。')],
        [('第一章·另一个白流苏', '白流苏在镜前梳妆。窗外是上海的黄昏，电车叮当作响。她看着镜中的自己——一个离婚的女人，寄居在亲戚家的客厅里。范柳原的出现是一个意外，但意外有时候就是命运的另一个名字。'), ('第二章·浅水湾', '浅水湾的旅店面向大海。白流苏和范柳原在这里度过了七天。他们谈情说爱，也谈战争与逃亡。范柳原说整个香港都会陷落，但她笑着说至少他们还有七天。'), ('第三章·倾城之后', '香港真的陷落了。炮火中的倾城之恋，反而让两人的手牵得更紧。他们在废墟中举行了最简单的婚礼——没有宾客，只有她和范柳原，还有一轮见证了一切的月亮。')],
        [('吃食', '上海人讲究吃。蟹粉小笼、腌笃鲜、糟钵斗，每一样都有每一样的讲究。张爱玲说她记得小时候家里的厨子能做一桌子好菜，但后来那些味道都随着时局散了。'), ('衣着', '旗袍是最懂女人的衣服。它包裹着身体，却把所有线条都暗示出来。旧上海的太太小姐们，每人都有几件像样的旗袍。'), ('街景', '电车叮当作响，黄包车夫在街角等客。弄堂里飘出油烟气，远处传来外滩的汽笛声。这就是上海——一个永远在告别又永远在重逢的城市。')],
        [('红玫瑰', '也许每一个男子全都有过这样的两个女人，至少两个。娶了红玫瑰，久而久之，红的变了墙上的一抹蚊子血，白的还是"床前明月光"；娶了白玫瑰，白的便是衣服上沾的一粒饭黏子，红的却是心口上一颗朱砂痣。'),
         ('白玫瑰', '振保的生命里有两个女人，一个是他的红玫瑰，一个是他的白玫瑰。一个是他的妻，一个是他的情妇。他觉得他是对的。可是在某个失眠的夜里，他忽然不确定了。'),],
        [('第一幕·面壁者', '联合国大会厅。罗辑在刺眼的灯光下被宣布为第四位面壁者。他不明白为什么是自己。只是一个普通的天体物理学家，普通的丈夫，普通的父亲。直到那个声音在他脑海中响起：面壁者，你的任务是欺骗全人类。'), ('第二幕·黑暗森林', '宇宙就是一座黑暗森林，每个文明都是带枪的猎人。罗辑终于理解了这句话的含义。他站在冰封的湖面上，对着虚空说出那个坐标——这是一个赌注，赌的是两个文明不敢互相暴露。他赌赢了。')],
        [('第一章·林云的球状闪电', '林云少校第一次向我展示球状闪电时，我们站在戈壁滩上，四周是烧焦的沙砾。她说球状闪电不是气象现象，而是一种宏观量子态。她的眼睛里有电光闪烁，那一刻我就知道，这个秘密会改变一切。'), ('第二章·新概念武器', '球状闪电本质上是一种宏观量子效应——它可以在任何地方出现，穿透任何已知的防御材料。如果能控制它，它将是人类历史上最可怕的武器。林云想用它来结束战争。而我只想用它来保护所爱的人。')],
        [('第一幕·启航', '联合政府大厅。全球直播。太阳即将在四百年内毁灭，人类做出了最疯狂的决定——带着地球一起逃离太阳系。一万座行星发动机同时点火，地球缓缓加速。告别了，太阳系。'),
         ('第二幕·地下城', '地球停转后，地面温度降至零下八十四度。人类搬入地下城。在这里，没有白天黑夜，只有人造的光。孩子们在课本上读到"天空是蓝色的"，但没有人亲眼见过。'),],
        [('第一幕·魔法部大厅', '魔法部的中庭，喷泉在清晨的阳光下闪烁。赫敏·格兰杰推开部长办公室的门，发现一份关于霍格沃茨魔法生物保护区的紧急提案——是由一个叫纽特·斯卡曼德的人发来的。办公室生活，开始了。'), ('第二幕·霍格沃茨调查', '赫敏和纽特一起来到霍格沃茨。城堡的走廊在烛光下显得格外神秘。禁林边缘出现了异常的魔法波动——一种从未被记录的魔法生物正在觉醒。如果处理不当，整个保护区都可能被毁掉。')],
        [('第一章·日记', '艾琳在霍格沃茨的旧书店里发现了一本泛黄的日记。扉页上只写了一行字："致未来的你——不要打开最后一页。"她当然打开了。从那天起，奇怪的事情开始发生在她身上。'),
         ('第二章·密室之声', '地下室的墙壁在低语。艾琳发现日记的前任主人是五十年前的一名学生，他在探索密室时失踪了。而那个密室，据说就在霍格沃茨的某个角落里。')],
        [('从咖啡馆到出版社', '一切始于爱丁堡的一家小咖啡馆。我在那里写下了第一个句子："哈利波特是一个男孩。"那时候我还不知道，这个句子会改变我的人生。'),
         ('关于想象力', '想象力是人类最强大的魔法。它能让你在一间小小的房间里，创造出整个宇宙。写作就是把想象力变成文字的魔法。每一个作家都是一个魔法师。')],
    ]

    work_ids = []
    chapter_count = 0
    for i, (uid, title, wtype, summary, tags, status) in enumerate(works_data):
        wid = execute(
            'INSERT INTO works (user_id, title, type, summary, tags, status) VALUES (%s, %s, %s, %s, %s, %s)',
            (uid, title, wtype, summary, tags, status)
        )
        work_ids.append(wid)

        chapters = chapters_data[i]
        if chapters:
            total_wc = 0
            for j, (ch_title, content) in enumerate(chapters):
                wc = len(content.replace(' ', '').replace('\n', ''))
                total_wc += wc
                execute(
                    'INSERT INTO chapters (work_id, chapter_no, title, content, word_count) VALUES (%s, %s, %s, %s, %s)',
                    (wid, j + 1, ch_title, content, wc)
                )
                chapter_count += 1
            execute('UPDATE works SET word_count = %s WHERE work_id = %s', (total_wc, wid))

    print(f'Seeded {len(work_ids)} works, {chapter_count} chapters.')

    # Set views for published works
    for i, (uid, title, wtype, summary, tags, status) in enumerate(works_data):
        if status == 'published' and work_ids[i]:
            views = random.randint(100, 5000)
            execute('UPDATE works SET views = %s WHERE work_id = %s', (views, work_ids[i]))


def seed_challenges():
    if _exists('challenges'):
        print('Challenges already seeded.')
        return

    today = date.today()
    challenges = [
        ('30天写作马拉松', '每天至少写500字，坚持30天！适合所有类型的写作爱好者。完成后可获得专属成就徽章。', today + timedelta(days=2), today + timedelta(days=32), 'upcoming', 500),
        ('古风诗词挑战', '以古风为题，每日创作一首诗词。不限格式，五言七言、词牌曲牌均可。', today - timedelta(days=5), today + timedelta(days=25), 'active', 100),
        ('科幻微小说大赛', '用300字以内的微小说，构建一个完整的科幻世界。最佳作品将获得首页推荐。', today - timedelta(days=2), today + timedelta(days=28), 'active', 200),
        ('每日千字计划', '千字文，每日一篇。题材不限，散文随笔最佳。练习观察生活，记录每一天。', today - timedelta(days=35), today - timedelta(days=5), 'ended', 1000),
    ]
    cids = []
    for title, desc, start, end, status, minw in challenges:
        cid = execute(
            'INSERT INTO challenges (title, description, start_date, end_date, status, min_words) VALUES (%s, %s, %s, %s, %s, %s)',
            (title, desc, start, end, status, minw)
        )
        cids.append(cid)
    print(f'Seeded {len(cids)} challenges.')
    return cids


def seed_participants():
    if _exists('challenge_participants'):
        print('Participants already seeded.')
        return

    users = [r['user_id'] for r in query('SELECT user_id FROM users')]
    challenges = query('SELECT challenge_id, status FROM challenges')

    count = 0
    for ch in challenges:
        # Assign 3-6 users per challenge
        n = min(len(users), random.randint(3, 6))
        for uid in random.sample(users, n):
            execute(
                'INSERT INTO challenge_participants (challenge_id, user_id) VALUES (%s, %s)',
                (ch['challenge_id'], uid)
            )
            count += 1
        execute(
            'UPDATE challenges SET participant_count = (SELECT COUNT(*) FROM challenge_participants WHERE challenge_id = %s) WHERE challenge_id = %s',
            (ch['challenge_id'], ch['challenge_id'])
        )
    print(f'Seeded {count} participants.')


def seed_checkins():
    if _exists('challenge_checkins'):
        print('Checkins already seeded.')
        return

    participants = query('''
        SELECT cp.participant_id, cp.challenge_id, c.start_date, c.end_date
        FROM challenge_participants cp
        JOIN challenges c ON cp.challenge_id = c.challenge_id
    ''')

    today = date.today()
    count = 0
    for p in participants:
        start = p['start_date']
        end = min(p['end_date'], today)
        days = (end - start).days
        if days <= 0:
            continue
        # Check in on 60-90% of days
        checkin_dates = set()
        n_checks = max(1, int(days * random.uniform(0.6, 0.9)))
        for _ in range(n_checks):
            d = start + timedelta(days=random.randint(0, max(0, days - 1)))
            checkin_dates.add(d)

        for d in checkin_dates:
            wc = random.randint(50, 2000)
            rid = execute(
                'INSERT IGNORE INTO challenge_checkins (participant_id, checkin_date, word_count, note) VALUES (%s, %s, %s, %s)',
                (p['participant_id'], d, wc, '今日写作打卡' if random.random() > 0.5 else '')
            )
            if rid:
                count += 1

        # Update participant stats
        stats = query('''
            SELECT COUNT(*) as days, COALESCE(SUM(word_count), 0) as total
            FROM challenge_checkins WHERE participant_id = %s
        ''', (p['participant_id'],), one=True)
        execute(
            'UPDATE challenge_participants SET checkin_days = %s, progress = %s WHERE participant_id = %s',
            (stats['days'], stats['total'], p['participant_id'])
        )

    print(f'Seeded {count} checkins.')


def seed_sessions():
    if _exists('writing_sessions'):
        print('Sessions already seeded.')
        return

    users = [r['user_id'] for r in query('SELECT user_id FROM users')]
    works = query('SELECT work_id, user_id FROM works')

    today = date.today()
    count = 0
    for uid in users:
        user_works = [w['work_id'] for w in works if w['user_id'] == uid]
        # 60 days of sessions
        for i in range(60):
            d = today - timedelta(days=i)
            # 70% chance of writing on any given day
            if random.random() > 0.7:
                continue
            # 1-3 sessions per day
            for _ in range(random.randint(1, 3)):
                wc = random.randint(50, 2500)
                work_id = random.choice(user_works) if user_works and random.random() > 0.3 else None
                dur = random.randint(10, 120)
                execute(
                    'INSERT INTO writing_sessions (user_id, work_id, word_count, duration, session_date) VALUES (%s, %s, %s, %s, %s)',
                    (uid, work_id, wc, dur, d)
                )
                count += 1
    print(f'Seeded {count} writing sessions.')


def seed_interactions():
    if _exists('comments'):
        print('Interactions already seeded.')
        return

    users = [r['user_id'] for r in query('SELECT user_id FROM users')]
    works = query("SELECT work_id, user_id FROM works WHERE status = 'published'")

    comments_data = [
        '写得真好，期待下一章！', '文笔优美，画面感很强。', '这个情节转折太妙了！',
        '角色塑造很立体，喜欢主角的性格。', '一口气读完了，意犹未尽。', '这段描写让我想到了自己。',
        '建议在对话部分可以更自然一些。', '节奏把握得很好，不拖沓。', '期待后续发展！',
        '作者的文字功底令人佩服。', '世界观设定很完整，引人入胜。', '每天追更，已经成为习惯了。',
        '这一章的结尾留下了很好的悬念。', '细节描写很到位，身临其境。', '有被治愈到，谢谢你的文字。',
        '开头略慢热，但后面越来越精彩。', '最期待的就是更新了！', '感情线处理得很细腻。',
        '语言很有个人风格，辨识度很高。', '读完之后久久不能平静。',
    ]

    # Comments
    c_count = 0
    for _ in range(30):
        w = random.choice(works)
        commenter = random.choice([u for u in users if u != w['user_id']])
        execute(
            'INSERT INTO comments (work_id, user_id, content) VALUES (%s, %s, %s)',
            (w['work_id'], commenter, random.choice(comments_data))
        )
        execute('UPDATE works SET comments_count = comments_count + 1 WHERE work_id = %s', (w['work_id'],))
        c_count += 1
    print(f'Seeded {c_count} comments.')

    # Likes
    l_count = 0
    for _ in range(40):
        w = random.choice(works)
        liker = random.choice([u for u in users if u != w['user_id']])
        r = query('SELECT 1 FROM work_likes WHERE user_id = %s AND work_id = %s', (liker, w['work_id']), one=True)
        if not r:
            execute('INSERT INTO work_likes (user_id, work_id) VALUES (%s, %s)', (liker, w['work_id']))
            execute('UPDATE works SET likes_count = likes_count + 1 WHERE work_id = %s', (w['work_id'],))
            l_count += 1
    print(f'Seeded {l_count} likes.')

    # Favorites
    f_count = 0
    for _ in range(20):
        w = random.choice(works)
        favoriter = random.choice([u for u in users if u != w['user_id']])
        r = query('SELECT 1 FROM favorites WHERE user_id = %s AND work_id = %s', (favoriter, w['work_id']), one=True)
        if not r:
            execute('INSERT INTO favorites (user_id, work_id) VALUES (%s, %s)', (favoriter, w['work_id']))
            execute('UPDATE works SET favorites_count = favorites_count + 1 WHERE work_id = %s', (w['work_id'],))
            f_count += 1
    print(f'Seeded {f_count} favorites.')

    # Follows
    follow_count = 0
    for u1 in users:
        for u2 in users:
            if u1 != u2 and random.random() > 0.5:
                r = query('SELECT 1 FROM follows WHERE follower_id = %s AND following_id = %s', (u1, u2), one=True)
                if not r:
                    execute('INSERT INTO follows (follower_id, following_id) VALUES (%s, %s)', (u1, u2))
                    follow_count += 1
    print(f'Seeded {follow_count} follows.')


def seed_notifications():
    if _exists('notifications'):
        print('Notifications already seeded.')
        return

    users = [r['user_id'] for r in query('SELECT user_id FROM users')]
    templates = [
        ('comment', '{} 评论了你的作品'),
        ('like', '{} 赞了你的作品'),
        ('favorite', '{} 收藏了你的作品'),
        ('follow', '{} 关注了你'),
        ('reply', '{} 回复了你的评论'),
    ]
    works = [r['work_id'] for r in query("SELECT work_id FROM works LIMIT 5")]

    count = 0
    for uid in users:
        for _ in range(random.randint(3, 8)):
            ntype, tmpl = random.choice(templates)
            other = random.choice([u for u in users if u != uid])
            other_name = query('SELECT username FROM users WHERE user_id = %s', (other,), one=True)['username']
            content = tmpl.format(other_name)
            related_id = random.choice(works) if ntype != 'follow' else other
            is_read = random.random() > 0.3
            execute(
                'INSERT INTO notifications (user_id, type, content, related_id, is_read) VALUES (%s, %s, %s, %s, %s)',
                (uid, ntype, content, related_id, is_read)
            )
            count += 1
    print(f'Seeded {count} notifications.')


def seed_relay_segments():
    if _exists('relay_segments'):
        print('Relay segments already seeded.')
        return

    users = [r['user_id'] for r in query('SELECT user_id FROM users')]
    challenges = query("SELECT challenge_id FROM challenges WHERE status != 'ended' LIMIT 1")
    if not challenges:
        return
    cid = challenges[0]['challenge_id']

    segments = [
        '清晨的第一缕阳光穿过古老的梧桐树叶，小镇在薄雾中缓缓苏醒。老陈像往常一样，推开了茶馆的木门。',
        '今天的茶馆格外热闹。几位老友围坐在靠窗的位置，讨论着镇上新来的说书人。据说他讲的三国故事与众不同，充满了对命运的哲思。',
        '我也好奇地走了进去。说书人是个四十来岁的中年人，眼神深邃。他讲的不只是故事，更像是在讲述自己的一段前世记忆。听众们都屏住了呼吸。',
        '当说书人讲到关羽败走麦城时，窗外忽然下起了暴雨。雨声、雷声与说书人的声音交织在一起，仿佛历史的悲鸣穿透了时空。老陈默默地给每个人添了一杯热茶。',
    ]
    for i, content in enumerate(segments):
        uid = users[i % len(users)]
        execute(
            'INSERT INTO relay_segments (challenge_id, user_id, content, segment_order) VALUES (%s, %s, %s, %s)',
            (cid, uid, content, i + 1)
        )
    print(f'Seeded {len(segments)} relay segments.')


def seed_reply_comments():
    """Add nested reply comments and pinned comments."""
    existing = query('SELECT COUNT(*) as cnt FROM comments WHERE parent_id IS NOT NULL')
    if existing[0]['cnt'] > 0:
        print('Reply comments already seeded.')
        return

    comments = query('SELECT comment_id, work_id, user_id, content FROM comments ORDER BY comment_id')
    if len(comments) < 5:
        print('Not enough comments for replies.')
        return

    users = [r['user_id'] for r in query('SELECT user_id FROM users')]
    replies = [
        '谢谢你的鼓励！会继续努力的。',
        '哈哈，你太客气了。',
        '说得好，我也有同感。',
        '感谢反馈，下次改进！',
        '这个建议很有价值，谢谢！',
    ]
    count = 0
    # Add 1-2 replies to the first 5 comments
    for c in comments[:5]:
        reply_user = random.choice([u for u in users if u != c['user_id']])
        rid = execute(
            'INSERT INTO comments (work_id, user_id, parent_id, content) VALUES (%s, %s, %s, %s)',
            (c['work_id'], reply_user, c['comment_id'], random.choice(replies))
        )
        execute('UPDATE works SET comments_count = comments_count + 1 WHERE work_id = %s', (c['work_id'],))
        count += 1
        if random.random() > 0.5:
            reply_user2 = random.choice([u for u in users if u != reply_user])
            execute(
                'INSERT INTO comments (work_id, user_id, parent_id, content) VALUES (%s, %s, %s, %s)',
                (c['work_id'], reply_user2, c['comment_id'], random.choice(replies))
            )
            execute('UPDATE works SET comments_count = comments_count + 1 WHERE work_id = %s', (c['work_id'],))
            count += 1

    # Pin one comment
    first_comment = comments[0]
    execute('UPDATE comments SET is_pinned = TRUE WHERE comment_id = %s', (first_comment['comment_id'],))

    print(f'Seeded {count} reply comments + 1 pinned comment.')


def seed_comment_likes():
    """Add likes on comments."""
    if _exists('comment_likes'):
        print('Comment likes already seeded.')
        return

    comments = query('SELECT comment_id, user_id FROM comments LIMIT 20')
    users = [r['user_id'] for r in query('SELECT user_id FROM users')]
    count = 0
    for c in comments:
        n_likes = random.randint(0, 3)
        likers = random.sample([u for u in users if u != c['user_id']], min(n_likes, len(users) - 1))
        for uid in likers:
            execute('INSERT IGNORE INTO comment_likes (user_id, comment_id) VALUES (%s, %s)', (uid, c['comment_id']))
            count += 1
    print(f'Seeded {count} comment likes.')


def seed_work_versions():
    """Create version snapshots for some works."""
    if _exists('work_versions'):
        print('Work versions already seeded.')
        return

    works = query("SELECT work_id FROM works WHERE status = 'published' LIMIT 5")
    count = 0
    for w in works:
        chapters = query('SELECT * FROM chapters WHERE work_id = %s ORDER BY chapter_no', (w['work_id'],))
        if not chapters:
            continue
        work_row = query('SELECT * FROM works WHERE work_id = %s', (w['work_id'],), one=True)
        snapshot = {
            'work': {k: (v.isoformat() if hasattr(v, 'isoformat') else v) for k, v in work_row.items()},
            'chapters': [{k: (v.isoformat() if hasattr(v, 'isoformat') else v) for k, v in ch.items()} for ch in chapters]
        }
        import json
        execute(
            'INSERT INTO work_versions (work_id, content_json, word_count) VALUES (%s, %s, %s)',
            (w['work_id'], json.dumps(snapshot, ensure_ascii=False), work_row['word_count'])
        )
        count += 1
    print(f'Seeded {count} work versions.')


def seed_ai_conversations():
    """Create sample AI conversation history."""
    if _exists('ai_conversations'):
        print('AI conversations already seeded.')
        return

    import uuid
    users = [r['user_id'] for r in query('SELECT user_id FROM users')][:3]
    conversations = [
        [
            ('user', '请帮我续写一段古风小说的开头，关于一个少年在长安城的夜晚。'),
            ('assistant', '长安城的夜，像一匹展开的黑缎，缀满了银色的星子。少年站在朱雀大街的尽头，听着远处传来的更鼓声。他叫李长风，今年十六岁，身上穿着一件洗得发白的青衫。这是他第一次独自来到长安。身上的银两已经花光了，但他不在乎。因为他知道，今夜过后，一切都将不同。'),
        ],
        [
            ('user', '帮我写一首关于秋天的五言绝句。'),
            ('assistant', '秋风起萧瑟，\n落叶满长安。\n雁过寒云远，\n孤灯照夜阑。'),
        ],
        [
            ('user', '我的小说主角是一个失忆的侦探，帮我构思一下故事大纲。'),
            ('assistant', '故事大纲：\n1. 开篇：侦探在医院醒来，发现自己失去了过去三年的记忆。桌上放着一张照片，照片里是他和一个陌生女人。\n2. 发现：他回到自己的事务所，发现三年前他接了一个案子——一个富商的失踪案。案子记录不完整，似乎被人刻意删除过。\n3. 追查：他开始调查那个照片里的女人，发现她是富商的妻子，而她也失踪了。\n4. 真相：他逐渐发现，自己在失忆前已经接近真相——富商并没有失踪，而是被人谋杀了。凶手就藏在他身边。\n5. 高潮：他发现自己失忆的原因并非意外，而是有人故意让他忘记。'),
        ],
    ]

    count = 0
    for uid in users:
        for conv in conversations[:random.randint(1, 3)]:
            session_key = str(uuid.uuid4())
            for role, content in conv:
                execute(
                    'INSERT INTO ai_conversations (user_id, session_key, role, content) VALUES (%s, %s, %s, %s)',
                    (uid, session_key, role, content)
                )
                count += 1
    print(f'Seeded {count} AI conversations.')


def seed_user_achievements():
    """Unlock achievements for users who meet the conditions."""
    if query('SELECT COUNT(*) as cnt FROM user_achievements')[0]['cnt'] > 0:
        print('User achievements already seeded.')
        return

    achievements = query('SELECT * FROM achievements')
    users = [r['user_id'] for r in query('SELECT user_id FROM users')]
    count = 0

    for uid in users:
        stats = {
            # 写作统计
            'word_count': query('SELECT COALESCE(SUM(word_count), 0) as v FROM works WHERE user_id = %s', (uid,), one=True)['v'],
            'likes': query('SELECT COALESCE(SUM(likes_count), 0) as v FROM works WHERE user_id = %s', (uid,), one=True)['v'],
            'comments': query('SELECT COALESCE(SUM(comments_count), 0) as v FROM works WHERE user_id = %s', (uid,), one=True)['v'],
            'works': query("SELECT COUNT(*) as v FROM works WHERE user_id = %s AND status = 'published'", (uid,), one=True)['v'],
            'checkin_days': query('''
                SELECT COUNT(DISTINCT checkin_date) as v FROM challenge_checkins cc
                JOIN challenge_participants cp ON cc.participant_id = cp.participant_id
                WHERE cp.user_id = %s
            ''', (uid,), one=True)['v'],
            'followers': query('SELECT COUNT(*) as v FROM follows WHERE following_id = %s', (uid,), one=True)['v'],
            # 阅读统计
            'books_read': query("SELECT COUNT(*) as v FROM reading_bookshelf WHERE user_id = %s AND shelf_group = 'completed'", (uid,), one=True)['v'],
            'reading_streak': query('SELECT COUNT(DISTINCT checkin_date) as v FROM reading_checkins WHERE user_id = %s', (uid,), one=True)['v'],
            'reading_hours': query('SELECT COALESCE(SUM(read_minutes), 0) as v FROM reading_time_logs WHERE user_id = %s', (uid,), one=True)['v'] // 60,
            'annotations': query('SELECT COUNT(*) as v FROM reading_annotations WHERE user_id = %s', (uid,), one=True)['v'],
            'highlights': query('SELECT COUNT(*) as v FROM reading_highlights WHERE user_id = %s', (uid,), one=True)['v'],
        }

        for ach in achievements:
            current = stats.get(ach['condition_type'], 0)
            if current >= ach['condition_value']:
                execute('INSERT IGNORE INTO user_achievements (user_id, achievement_id) VALUES (%s, %s)',
                        (uid, ach['achievement_id']))
                count += 1

    print(f'Seeded {count} user achievements.')


if __name__ == '__main__':
    print('Seeding Inkstone database...')
    seed_achievements()
    seed_users()
    seed_works()
    seed_challenges()
    seed_participants()
    seed_checkins()
    seed_sessions()
    seed_interactions()
    seed_reply_comments()
    seed_comment_likes()
    seed_work_versions()
    seed_ai_conversations()
    seed_notifications()
    seed_relay_segments()
    seed_user_achievements()

    # Import poems library
    from scripts.crawl_poems import import_poems
    import_poems()

    # Import materials library
    from scripts.seed_materials import import_materials
    import_materials()

    # Import daily prompts
    from scripts.seed_daily_prompts import import_daily_prompts
    import_daily_prompts()

    # 注：书库/外部书籍导入已下线（P2），seed 不再导入小说

    # Import real data from public sources
    from scripts.import_real_data import import_poems_from_github, import_public_domain_books, import_real_prompts
    import_poems_from_github(limit_per_source=100)
    import_public_domain_books()
    import_real_prompts()

    print('Seeding complete!')
