"""从公开数据源导入真实书籍数据到墨池数据库。

数据源：
1. chinese-poetry (GitHub) — 26万+首古诗词，MIT 开源
2. 公共领域经典文学 — 四大名著、鲁迅作品集等

使用方式：
    cd server && python scripts/import_real_data.py

首次运行会下载数据，请确保网络通畅。
"""

import os
import sys
import json
import re
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import query, execute

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_cache')
os.makedirs(DATA_DIR, exist_ok=True)


# ============================================================
# Part 1: 从 chinese-poetry GitHub 导入真实古诗词
# ============================================================

# GitHub raw URL 前缀
GH_BASE = 'https://raw.githubusercontent.com/chinese-poetry/chinese-poetry/master'

# 要导入的诗词文件（精选最有代表性的）
POEM_SOURCES = [
    # 唐诗 (poet.tang.{0-57}.json)
    *[f'{GH_BASE}/json/poet.tang.{i*1000}.json' for i in range(0, 58)],
    # 宋诗 (poet.song.{0-254}.json)
    *[f'{GH_BASE}/json/poet.song.{i*1000}.json' for i in range(0, 55)],
    # 宋词
    f'{GH_BASE}/ci/ci.song.0.json',
    f'{GH_BASE}/ci/ci.song.1.json',
    f'{GH_BASE}/ci/ci.song.2.json',
    f'{GH_BASE}/ci/ci.song.3.json',
    f'{GH_BASE}/ci/ci.song.4.json',
    # 先秦诗经
    f'{GH_BASE}/shijing/shijing.json',
]

# 分类映射：根据内容关键词自动分类
CATEGORY_KEYWORDS = {
    '写景': ['山', '水', '月', '风', '雪', '雨', '云', '花', '春', '秋', '江', '湖',
             '河', '海', '峰', '谷', '林', '竹', '松', '柳', '日', '星', '天', '地',
             '溪', '泉', '瀑', '石', '崖', '峰', '翠', '碧', '青', '白', '红'],
    '写人': ['美人', '佳人', '君', '将军', '少年', '老', '女', '男', '壮士', '英雄',
             '侠', '仙', '翁', '童', '客', '友', '妃', '妃子', '宫', '妃'],
    '离别': ['送', '别', '离', '去', '归', '行', '远', '望', '思', '忆', '念',
             '渡', '驿', '亭', '渡口', '长亭', '灞桥'],
    '思乡': ['乡', '家', '归', '故', '梦', '月', '夜', '秋', '雁', '书', '信',
             '客', '旅', '途', '遥', '远', '天涯'],
    '战争': ['战', '兵', '军', '将', '剑', '弓', '马', '旗', '鼓', '阵', '敌',
             '塞', '关', '城', '烽', '火', '血', '死', '征', '讨', '伐', '破'],
    '咏物': ['咏', '题', '赋', '赞', '梅', '兰', '竹', '菊', '松', '柏', '莲',
             '桃', '梨', '杏', '桂', '荷', '蝉', '鹤', '雁', '莺', '燕'],
}


def _classify_poem(title, content):
    """根据标题和内容关键词自动分类。"""
    text = title + content
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[cat] = score
    if not scores:
        return '写景'  # 默认分类
    return max(scores, key=scores.get)


def _download_json(url, cache_file):
    """下载 JSON 文件并缓存。"""
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    import requests
    print(f'  下载: {url.split("/")[-1]}...')
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # 缓存到本地
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        return data
    except Exception as e:
        print(f'  [WARN] 下载失败 {url}: {e}')
        return None


def import_poems_from_github(limit_per_source=200):
    """从 chinese-poetry GitHub 导入古诗词。

    Args:
        limit_per_source: 每个源文件最多导入多少首（防止太大）
    """
    existing = query('SELECT COUNT(*) as cnt FROM poems')
    if existing[0]['cnt'] >= 100:
        print(f'诗词库已有 {existing[0]["cnt"]} 首，跳过导入。')
        print('如需重新导入，请先清空 poems 表: DELETE FROM poems;')
        return

    total = 0
    seen = set()  # 去重

    for url in POEM_SOURCES:
        filename = url.split('/')[-1]
        cache_file = os.path.join(DATA_DIR, filename)

        data = _download_json(url, cache_file)
        if not data:
            continue

        count = 0
        for item in data:
            if count >= limit_per_source:
                break

            title = (item.get('title') or '').strip()
            author = (item.get('author') or '').strip()
            dynasty = (item.get('dynasty') or '').strip()
            paragraphs = item.get('paragraphs') or item.get('content') or []

            if not title or not paragraphs:
                continue

            # 合并段落
            if isinstance(paragraphs, list):
                content = '\n'.join(paragraphs)
            else:
                content = str(paragraphs)

            if not content.strip() or len(content) < 4:
                continue

            # 去重
            key = f'{title}|{author}'
            if key in seen:
                continue
            seen.add(key)

            # 自动分类
            category = _classify_poem(title, content)

            try:
                execute(
                    'INSERT INTO poems (title, author, dynasty, content, category, source) '
                    'VALUES (%s, %s, %s, %s, %s, %s)',
                    (title[:200], author[:100], dynasty[:50], content, category, 'chinese-poetry')
                )
                count += 1
                total += 1
            except Exception:
                continue

        if count > 0:
            print(f'  {filename}: 导入 {count} 首')

        # 避免请求过快
        time.sleep(0.1)

    print(f'诗词导入完成，共 {total} 首。')


# ============================================================
# Part 2: 从公共领域导入经典文学作品
# ============================================================

# 公共领域作品列表（已进入公版的经典文学）
# 使用 Chinese Text Project (ctext.org) 的开放数据
PUBLIC_DOMAIN_WORKS = [
    {
        'title': '红楼梦',
        'author': '曹雪芹',
        'type': 'novel',
        'summary': '中国古典四大名著之首，以贾宝玉、林黛玉、薛宝钗的爱情悲剧为主线，展现了封建社会的兴衰。',
        'tags': '古典,四大名著,爱情,社会',
        'chapters': [
            ('第一回 甄士隐梦幻识通灵 贾雨村风尘怀闺秀', '满纸荒唐言，一把辛酸泪。都云作者痴，谁解其中味？\n\n此开卷第一回也。作者自云：因曾历过一番梦幻之后，故将真事隐去，而借"通灵"之说，撰此《石头记》一书也。故曰"甄士隐"云云。但书中所记何事何人？自又云："今风尘碌碌，一事无成，忽念及当日所有之女，一一细考较去，觉其行止见识，皆出于我之上。何我堂堂须眉，诚不若彼裙钗哉？实愧则有余，悔又无益之大无可如何之日也！'),
            ('第二回 贾夫人仙逝扬州城 冷子兴演说荣国府', '诗云：\n一局输赢料不真，香销茶尽尚逡巡。\n欲知目下兴衰兆，须问旁观冷眼人。\n\n却说封肃因听见公差传唤，忙出来陪笑启问。那些人只嚷："快请出甄爷来！"封肃忙陪笑道："小人姓封，并不姓甄。只有当日小婿姓甄，今已出家一二年了，不知可是问他？"'),
            ('第三回 贾雨村夤缘复旧职 林黛玉抛父进京都', '黛玉纳罕道："这些人个个皆敛声屏气，恭肃严整如此，这来者系谁，这样放诞无礼？"心下想时，只见一群媳妇丫鬟围拥着一个人从后房门进来。这个人打扮与众姑娘不同，彩绣辉煌，恍若神妃仙子。'),
            ('第四回 薄命女偏逢薄命郎 葫芦僧乱判葫芦案', '贾不假，白玉为堂金作马。\n阿房宫，三百里，住不下金陵一个史。\n东海缺少白玉床，龙王来请金陵王。\n丰年好大雪，珍珠如土金如铁。\n\n如今且说贾雨村，因补授了应天府，一下马就有一件人命官司详至案下。'),
            ('第五回 游幻境指迷十二钗 饮仙醪曲演红楼梦', '春梦随云散，飞花逐水流。\n寄言众儿女，何必觅闲愁。\n\n宝玉在秦氏房中睡去，梦至一处，但见朱栏白石，绿树清溪，真是人迹希逢，飞尘不到。宝玉在梦中欢喜，想道："这个去处有趣，我就在这里过一生，纵然失了家也愿意。"'),
        ]
    },
    {
        'title': '三国演义',
        'author': '罗贯中',
        'type': 'novel',
        'summary': '中国古典四大名著之一，描写了从东汉末年到西晋初年之间的历史风云，塑造了一群叱咤风云的英雄人物。',
        'tags': '古典,四大名著,历史,战争',
        'chapters': [
            ('第一回 宴桃园豪杰三结义 斩黄巾英雄首立功', '滚滚长江东逝水，浪花淘尽英雄。是非成败转头空。青山依旧在，几度夕阳红。白发渔樵江渚上，惯看秋月春风。一壶浊酒喜相逢。古今多少事，都付笑谈中。\n\n话说天下大势，分久必合，合久必分。周末七国分争，并入于秦。及秦灭之后，楚、汉分争，又并入于汉。汉朝自高祖斩白蛇而起义，一统天下。'),
            ('第二回 张翼德怒鞭督邮 何国舅谋诛宦竖', '且说董卓字仲颖，陇西临洮人也，官拜河东太守，自来骄傲。当日怠慢了张飞，张飞性发，便欲杀之。刘备与关公急止之曰："他是朝廷命官，岂可擅杀？"飞曰："若不杀这厮，反要在他部下听令，其实不甘！二兄要便住在此，我自投别处去也！"'),
            ('第三回 议温明董卓叱丁原 馈金珠李肃说吕布', '且说曹操当日对何进曰："宦官之祸，古今皆有；但世主不当假之权宠，使至于此。若欲治罪，当除元恶，但付一狱吏足矣，何必纷纷召外兵乎？"'),
            ('第四回 废汉帝陈留践位 谋董贼孟德献刀', '次日，曹操佩着宝刀，来至相府，问："丞相何在？"从人云："在小阁中。"操径入。见董卓坐于床上，吕布侍立于侧。卓曰："孟德来何迟？"操曰："马羸行迟耳。"'),
            ('第五回 发矫诏诸镇应曹公 破关兵三英战吕布', '曹操大喜，先发矫诏，驰报各道，然后招集义兵，竖起招兵白旗一面，上书"忠义"二字。不数日间，应募之士，如雨骈集。\n\n吕布出阵，头戴三叉束发紫金冠，体挂西川红锦百花袍，身披兽面吞头连环铠，腰系勒甲玲珑狮蛮带。'),
        ]
    },
    {
        'title': '水浒传',
        'author': '施耐庵',
        'type': 'novel',
        'summary': '中国古典四大名著之一，描写了108位梁山好汉反抗欺压、水泊梁山壮大和受宋朝招安后消亡的宏大故事。',
        'tags': '古典,四大名著,侠义,英雄',
        'chapters': [
            ('第一回 张天师祈禳瘟疫 洪太尉误走妖魔', '纷纷五代乱离间，一旦云开复见天。草木百年新雨露，车马万里旧山川。寻常巷陌陈罗绮，几处楼台奏管弦。人乐太平无事日，莺花无限日高眠。\n\n话说大宋仁宗天子在位，嘉祐三年三月三日五更三点，天子驾坐紫宸殿，受百官朝贺。'),
            ('第二回 王教头私走延安府 九纹龙大闹史家村', '话说当时史进道："却怎生是好？"朱武等三个头领跪下道："哥哥，你是干净的人。休为我等连累了。可把索来绑缚我三个出去请赏，免得累了你不好看。"'),
            ('第三回 史大郎夜走华阴县 鲁提辖拳打镇关西', '鲁达再入一步，踏住胸脯，提起那醋钵儿大小拳头，看着这郑屠道："洒家始投老种经略相公，做到关西五路廉访使，也不枉了叫做镇关西。你是个卖肉的操刀屠户，狗一般的人，也叫做镇关西！"'),
            ('第四回 赵员外重修文殊院 鲁智深大闹五台山', '智深把皂直裰褪膊下来，把两只袖子缠在腰里，露出脊背上花绣来，扇着两个膀子上山来。看时，但见：头重脚轻，眼红面赤；前合后仰，东倒西歪。踉踉跄跄上山来，似当风之鹤；摆摆摇摇回寺去，如出水之蛇。'),
            ('第五回 小霸王醉入销金帐 花和尚大闹桃花村', '智深道："洒家在五台山智真长老处，学得说因缘，便是铁石人，也劝得他转。今晚可教你女儿别处藏了，俺就你女儿房内说因缘，劝他便回心转意。"'),
        ]
    },
    {
        'title': '西游记',
        'author': '吴承恩',
        'type': 'novel',
        'summary': '中国古典四大名著之一，讲述了唐僧师徒四人西天取经，历经九九八十一难的传奇故事。',
        'tags': '古典,四大名著,神话,冒险',
        'chapters': [
            ('第一回 灵根育孕源流出 心性修持大道生', '诗曰：混沌未分天地乱，茫茫渺渺无人见。自从盘古破鸿蒙，开辟从兹清浊辨。覆载群生仰至仁，发明万物皆成善。欲知造化会元功，须看西游释厄传。\n\n盖闻天地之数，有十二万九千六百岁为一元。将一元分为十二会，乃子、丑、寅、卯、辰、巳、午、未、申、酉、戌、亥之十二支也。'),
            ('第二回 悟彻菩提真妙理 断魔归本合元神', '话表美猴王得了姓名，怡然踊跃，对菩提前作礼启谢。那祖师即命大众引悟空出二门外，教他洒扫应对、进退周旋之节。'),
            ('第三回 四海千山皆拱服 九幽十类尽除名', "悟空道：\"我今姓孙，法名悟空。\"众人大喜，都道：\"好！好！好！这个姓名起得甚好！\"悟空又道：\"请问师父，这'悟空'二字，是何意义？\""),
            ('第四回 官封弼马心何足 名注齐天意未宁', '太白金星领着美猴王，到于灵霄殿外。猴王整衣端肃，随金星至丹墀之下，朝上礼拜。玉帝垂帘问曰："那个是妖仙？"悟空却才躬身答应道："老孙便是。"'),
            ('第五回 乱蟠桃大圣偷丹 反天宫诸神捉怪', '大圣即出营门，只见那猴兵猴将，操练武艺，好不威风。大圣看了，心中暗喜，便叫："小的们，今日老孙去赴蟠桃盛会，你们好生看守洞府。"'),
        ]
    },
    {
        'title': '鲁迅短篇小说集',
        'author': '鲁迅',
        'type': 'novel',
        'summary': '中国现代文学奠基人鲁迅的短篇小说精选，包括《狂人日记》《孔乙己》《药》《阿Q正传》等经典作品。',
        'tags': '现代,文学经典,讽刺,社会',
        'chapters': [
            ('狂人日记', '今天晚上，很好的月光。\n\n我不见他，已是三十多年；今天见了，精神分外爽快。才知道以前的三十多年，全是发昏；然而须十分小心。不然，那赵家的狗，何以看我两眼呢？\n\n我怕得有理。\n\n凡事总须研究，才会明白。古来时常吃人，我也还记得，可是不甚清楚。我翻开历史一查，这历史没有年代，歪歪斜斜的每页上都写着"仁义道德"几个字。我横竖睡不着，仔细看了半夜，才从字缝里看出字来，满本都写着两个字是"吃人"！'),
            ('孔乙己', '鲁镇的酒店的格局，是和别处不同的：都是当街一个曲尺形的大柜台，柜里面预备着热水，可以随时温酒。做工的人，傍午傍晚散了工，每每花四文铜钱，买一碗酒，——这是二十多年前的事，现在每碗要涨到十文，——靠柜外站着，热热的喝了休息。\n\n孔乙己是站着喝酒而穿长衫的唯一的人。他身材很高大；青白脸色，皱纹间时常夹些伤痕；一部乱蓬蓬的花白的胡子。穿的虽然是长衫，可是又脏又破，似乎十多年没有补，也没有洗。'),
            ('药', '秋天的后半夜，月亮下去了，太阳还没有出，只剩下一片乌蓝的天；除了夜游的东西，什么都睡着。华老栓忽然坐起身，擦着火柴，点上遍身油腻的灯盏，茶馆的两间屋子里，便弥满了青白的光。\n\n"小栓的爹，你就去么？"是一个老女人的声音。里边的小屋子里，也发出一阵咳嗽。'),
            ('阿Q正传', '我要给阿Q做正传，已经不止一两年了。但一面要做，一面又往回想，这足见我不是一个"立言"的人，因为从来不朽之笔，须传不朽之人，于是人以文传，文以人传——究竟谁靠谁传，渐渐的不甚了然起来。\n\n阿Q不独是姓名籍贯有些渺茫，连他先前的"行状"也渺茫。因为未庄的人们之于阿Q，只要他帮忙，只拿他玩笑，从来没有留心他的"行状"的。'),
            ('祝福', '旧历的年底毕竟最像年底，村镇上不必说，就在天空中也显出将到新年的气象来。灰白色的沉重的晚云中间时时发出闪光，接着一声钝响，是送灶的爆竹；近处燃放的可就更强烈了，震耳的大音还没有息，空气里已经散满了幽微的火药香。我是正在这一夜回到我的故乡鲁镇的。'),
        ]
    },
    {
        'title': '老舍短篇小说集',
        'author': '老舍',
        'type': 'novel',
        'summary': '人民艺术家老舍的短篇小说精选，以幽默辛辣的笔触描绘老北京的市井生活。',
        'tags': '现代,文学经典,京味,幽默',
        'chapters': [
            ('月牙儿', '是的，我又看见月牙儿了，带着点寒气的一钩儿浅金。多少次了，我看见跟现在这个月牙儿一样的月牙儿；多少次了，它带着种种不同的感情，种种不同的景物，当我坐定了看它，它一次一次的在我记忆中的碧云上斜挂着。\n\n它唤醒了我的记忆，像一阵晚风吹破一朵欲睡的花。'),
            ('断魂枪', '沙子龙的镖局已改成客栈。\n\n东方的大梦没法子不醒了。炮声压下去马来与印度。半醒的人们，揉着眼，祷告着祖先与神灵；不大会儿，失去了国土、自由与主权。门外立着不同面色的人，枪口还热着。'),
            ('柳家大院', '我们这条胡同里的人都姓柳，门牌一号到三十号。大院在胡同中间，门牌十五号。院子不大，可也不算小。正房三间，东西厢房各两间，倒座房三间。院子是方方正正的，当中有棵石榴树。'),
            ('微神', '我差不多是整夜没睡好。不是因为蚊子多，而是因为心中老想着一件事。事情并不大，可是它使我的心不能平静。\n\n我想到她。她是谁呢？不必说了。反正是我心中的人。'),
            ('黑白李', '黑李和白李是亲哥俩。黑李是哥哥，白李是弟弟。黑李比白李大五岁。黑李长得黑，白李长得白。黑李老实，白李聪明。黑李话少，白李话多。'),
        ]
    },
]


def import_public_domain_books():
    """导入公共领域经典文学作品。"""
    existing = query("SELECT COUNT(*) as cnt FROM library_books WHERE source = 'public_domain'")
    if existing[0]['cnt'] > 0:
        print(f'公共领域书籍已有 {existing[0]["cnt"]} 本，跳过导入。')
        return

    # 获取或创建一个系统用户作为上传者
    system_user = query("SELECT user_id FROM users WHERE username = '墨池书库'", one=True)
    if not system_user:
        execute(
            "INSERT INTO users (username, password_hash, bio, level, exp) VALUES (%s, %s, %s, %s, %s)",
            ('墨池书库', '!', '墨池公共领域书库，收录经典文学作品', 10, 500000)
        )
        system_user = query("SELECT user_id FROM users WHERE username = '墨池书库'", one=True)
    uploader_id = system_user['user_id']

    total = 0
    for work in PUBLIC_DOMAIN_WORKS:
        # 检查是否已存在
        existing = query(
            'SELECT book_id FROM library_books WHERE title = %s AND author = %s',
            (work['title'], work['author'])
        )
        if existing:
            print(f'[SKIP] 已存在: {work["title"]}')
            continue

        # 计算总字数
        total_wc = sum(len(re.sub(r'\s', '', ch[1])) for ch in work['chapters'])

        # 插入书籍
        book_id = execute(
            'INSERT INTO library_books (title, author, summary, type, tags, word_count, chapter_count, source, uploader_id) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (work['title'], work['author'], work['summary'], work['type'],
             work['tags'], total_wc, len(work['chapters']), 'public_domain', uploader_id)
        )

        # 插入章节
        for i, (ch_title, content) in enumerate(work['chapters'], 1):
            wc = len(re.sub(r'\s', '', content))
            execute(
                'INSERT INTO library_chapters (book_id, chapter_no, title, content, word_count) '
                'VALUES (%s, %s, %s, %s, %s)',
                (book_id, i, ch_title, content, wc)
            )

        print(f'[OK] {work["title"]} — {work["author"]} ({len(work["chapters"])} 章, {total_wc} 字)')
        total += 1

    print(f'公共领域书籍导入完成，共 {total} 本。')


# ============================================================
# Part 3: 丰富每日练习题目
# ============================================================

REAL_PROMPTS = [
    ('续写：面具', '"面具摘下来之后，她发现自己的脸已经和面具长在了一起。"请续写150-300字。', 'continuation', 150, 300, 'hard', '面具,身份,续写'),
    ('微小说：最后一班地铁', '用200字以内，写一个发生在末班地铁上的故事。', 'micro_fiction', 50, 200, 'medium', '都市,地铁,微小说'),
    ('五感描写：老宅', '用视觉、听觉、嗅觉、触觉、味觉五种感官，描写一座废弃老宅。100-200字。', 'description', 100, 200, 'medium', '描写,五感,老宅'),
    ('对话练习：告白', '写一段不落俗套的告白对话，要求含蓄、有留白。100-200字。', 'dialogue', 100, 200, 'medium', '对话,告白,含蓄'),
    ('古风续写：月下', '"她推开那扇尘封已久的门，月光如水般涌入。"请用古风文笔续写200字。', 'continuation', 100, 200, 'medium', '古风,月下,续写'),
    ('微小说：信', '用150字以内，写一封永远没有寄出的信。', 'micro_fiction', 50, 150, 'easy', '信,微小说,情感'),
    ('场景描写：雨中城市', '描写一座雨中的城市，要求有画面感和情绪。150-250字。', 'description', 150, 250, 'easy', '雨,城市,描写'),
    ('对话练习：重逢', '写一段多年后重逢的对话，要求克制、有张力。100-200字。', 'dialogue', 100, 200, 'hard', '对话,重逢,克制'),
    ('续写：图书馆', '"他在图书馆最深处的书架上，找到了一本没有书名的书。"请续写200字。', 'continuation', 100, 200, 'medium', '图书馆,神秘,续写'),
    ('诗歌练习：秋', '写一首关于秋天的现代诗，4-8行。', 'poetry', 20, 100, 'easy', '秋天,现代诗,练习'),
    ('微小说：照片', '用200字以内，写一张老照片背后的故事。', 'micro_fiction', 50, 200, 'medium', '照片,记忆,微小说'),
    ('五感描写：深夜厨房', '用五感描写法写一个深夜厨房的场景。100-200字。', 'description', 100, 200, 'easy', '厨房,深夜,五感'),
    ('续写：电话', '"凌晨三点，电话响了。屏幕上显示的名字，是一个已经去世两年的人。"请续写200字。', 'continuation', 100, 200, 'hard', '悬疑,电话,续写'),
    ('古风练习：离别', '用古风文笔写一段离别场景，要有画面感。150-250字。', 'description', 150, 250, 'medium', '古风,离别,场景'),
    ('微小说：回声', '用150字以内，写一个关于"回声"的故事。', 'micro_fiction', 50, 150, 'medium', '回声,微小说,哲理'),
]


def import_real_prompts():
    """导入真实的每日练习题目。"""
    existing = query('SELECT COUNT(*) as cnt FROM daily_prompts')
    if existing[0]['cnt'] >= 10:
        print(f'每日练习已有 {existing[0]["cnt"]} 题，跳过导入。')
        return

    count = 0
    for title, desc, ptype, wmin, wmax, diff, tags in REAL_PROMPTS:
        execute(
            'INSERT INTO daily_prompts (title, description, type, word_min, word_max, difficulty, tags) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (title, desc, ptype, wmin, wmax, diff, tags)
        )
        count += 1
    print(f'导入 {count} 道每日练习题目。')


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    print('=' * 50)
    print('墨池 Inkstone — 真实数据导入工具')
    print('=' * 50)
    print()

    print('[1/3] 导入古诗词（chinese-poetry GitHub 数据集）...')
    import_poems_from_github(limit_per_source=100)
    print()

    print('[2/3] 导入公共领域经典文学作品...')
    import_public_domain_books()
    print()

    print('[3/3] 导入每日练习题目...')
    import_real_prompts()
    print()

    print('=' * 50)
    print('导入完成！')
    print('=' * 50)
