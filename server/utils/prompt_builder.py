"""所有 AI Prompt 模板集中管理"""


def build_references_text(references):
    """把前端传来的 references（素材/诗词/句子）格式化为注入文本；非法/空返回 None。"""
    if not references:
        return None
    lines = []
    for r in references[:6]:
        if isinstance(r, dict):
            content = str(r.get('content') or '').strip()
            if not content:
                continue
            label = str(r.get('type') or r.get('category') or '素材')
        elif isinstance(r, str) and r.strip():
            content = r.strip()
            label = '素材'
        else:
            continue
        lines.append(f'- [{label}] {content[:500]}')
    if not lines:
        return None
    block = '\n'.join(lines)
    return (
        '\n\n=== 参考素材（借鉴其中的意象/措辞/氛围，仅在契合时化用，不要照抄整句或整段）===\n'
        + block
    )[:4000]


def build_continue(content, style='现代', context=None, references=None):
    """续写 prompt。context：作品设定参考（W2a）；references：素材/诗词注入（W4a）。"""
    system = f'你是一位精通{style}风格的专业作家。请根据用户提供的上文，用{style}风格续写后续内容。保持文风一致，情节自然衔接。续写200-500字。'
    user = f'请续写以下内容（只续写，不要重写上文）：\n\n{content}'
    if context:
        user += (
            '\n\n=== 作品设定参考（仅用于保持世界观/人设/剧情连贯，'
            '不得当作上文续写，也不得照抄）===\n' + context
        )
    ref_block = build_references_text(references)
    if ref_block:
        user += ref_block
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user}
    ]


def build_inspire(keywords):
    return [
        {'role': 'system', 'content': '你是一位创意写作导师，擅长从关键词中挖掘故事灵感。请生成3-5个故事创意，每个包含：标题、一句话梗概、适合的体裁。'},
        {'role': 'user', 'content': f'请根据以下关键词生成故事灵感：{keywords}'}
    ]


def build_outline(theme):
    return [
        {'role': 'system', 'content': '你是一位资深故事架构师。请根据用户提供的主题，生成一个完整的分章大纲，包含8-15个章节，每章有标题和简要内容说明。'},
        {'role': 'user', 'content': f'请为以下故事主题生成章节大纲：{theme}'}
    ]


def build_character(story_context):
    return [
        {'role': 'system', 'content': '你是一位角色设计师。请为给定的故事背景生成1-2个角色设定卡片，包含：姓名、性别、年龄、外貌特征、性格描述、背景故事、角色弧光、口头禅。'},
        {'role': 'user', 'content': f'故事背景：{story_context}\n\n请生成角色设定。'}
    ]


def build_polish(text, mode='流畅', references=None):
    mode_map = {
        '流畅': '使文字更加流畅自然',
        '文艺': '使文字更加文艺优美，增添诗意',
        '有力': '使文字更加简洁有力，增强节奏感',
        '简洁': '精简文字，去除冗余表达'
    }
    instruction = mode_map.get(mode, '优化文字表达')
    user = f'请润色以下文字（{mode}模式）：\n\n{text}'
    ref_block = build_references_text(references)
    if ref_block:
        user += ref_block
    return [
        {'role': 'system', 'content': f'你是一位文字编辑专家。{instruction}。保持原意不变，只优化表达方式。'},
        {'role': 'user', 'content': user}
    ]


def build_fix(text):
    """错字/病句检查：返回结构化 JSON（原文→建议）供一键替换。"""
    return [
        {'role': 'system', 'content': (
            '你是一位严谨的文字校对编辑，负责检查错别字与病句。'
            '只检查错字（字形相近/读音相近的误用）、用词不当、语病（搭配不当/成分残缺/杂糅/歧义）。'
            '不要改写作风格，不要为"换词更好"而建议，只在确有错误时给出。\n'
            '返回纯 JSON 数组（不要 markdown 代码块），每项格式：\n'
            '{"original":"原文中的错误片段（务必与原文一字不差）","suggestion":"建议改为","reason":"原因，一句话"}'
        )},
        {'role': 'user', 'content': f'请检查以下文字：\n\n{text}'}
    ]


def build_interpret(text):
    """翻译/解释选中内容（古诗句→白话释义+意境+用典）。"""
    return [
        {'role': 'system', 'content': (
            '你是一位博学的古典文学讲解者，同时熟悉现代白话文。'
            '请解释以下内容：1.【释义】用白话把意思讲清楚；2.【意境】一句话概括所传达的画面或情绪；'
            '3.【用典/出处】如有典故或出处请注明，没有则省略。'
            '语言简洁有温度，总长度控制在 250 字以内。'
        )},
        {'role': 'user', 'content': f'{text}'}
    ]


def build_find_lines(intent, pool_text):
    """意境找句：从素材池中挑最贴合意境的条目 + 创作几句原创句子。"""
    system = (
        '你是一位精通古典诗词与现代文学素材的选句编辑。'
        '用户会用一句话描述想描写的意境，你需要从素材库中挑选最贴合的条目。\n'
        '返回纯 JSON 对象（不要 markdown 代码块），格式：\n'
        '{"picks":[{"idx":3,"reason":"贴合原因一句话"}],"created":["原创句子1","原创句子2"]}\n'
        '要求：\n'
        '1. picks 挑选 3-6 条，idx 必须来自素材清单中的序号，reason 说明意境/意象吻合点；\n'
        '2. created 生成 2-3 句贴合意境的原创佳句（可以是现代诗或古风），不要引用清单原文；\n'
        '3. 若素材库确实没有贴合的，picks 可返回空数组，但 created 必须给出原创句。'
    )
    user = f'用户想描写的意境：{intent}\n\n=== 素材清单（[序号] 类型 标题（作者）：内容）===\n{pool_text}'
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]


def build_prompt_suggestion(context):
    return [
        {'role': 'system', 'content': '你是一位写作指导。用户卡文了，请根据当前情节提供3-5个剧情走向建议，每个包含：方向描述、可能的冲突点或反转。帮用户打开思路。'},
        {'role': 'user', 'content': f'我卡文了，当前情节：\n\n{context}\n\n请给我一些剧情走向建议。'}
    ]


def build_style_analysis(works_text):
    return [
        {'role': 'system', 'content': '你是一位文学风格分析师。根据用户的作品内容，分析其写作风格，返回纯JSON对象（不要markdown代码块），包含5个维度0-100的分数：文艺(文学性/修辞)、朴实(直白/简洁)、幽默(诙谐/趣味)、激昂(情感强度/节奏)、忧郁(沉静/感伤)。只返回JSON，不要其他文字。'},
        {'role': 'user', 'content': f'请分析以下作品的写作风格，返回5维度JSON：\n\n{works_text}'}
    ]


def build_monthly_report(stats_data):
    return [
        {'role': 'system', 'content': '你是一位温暖的写作教练。根据用户的月度写作数据，写一份200-400字的月度报告。内容包含：本月亮点、相比上月的进步/退步分析、写作习惯建议、下月鼓励语。用温暖鼓励的语气，中文撰写。'},
        {'role': 'user', 'content': f'以下是我本月的写作数据，请生成月度报告：\n\n{stats_data}'}
    ]


def build_character_graph(chapter_text):
    return [
        {'role': 'system', 'content': '你是一位文学分析师。从作品文本中提取所有角色及其关系，返回纯JSON对象（不要markdown代码块）：{"nodes":[{"name":"角色名","category":"主角/配角/反派","description":"简介"}],"edges":[{"source":"角色名","target":"角色名","label":"关系描述"}]}。注意：edges中的source和target必须与nodes中的name完全一致。category只能是主角/配角/反派。'},
        {'role': 'user', 'content': f'请提取以下文本中的角色和关系：\n\n{chapter_text}'}
    ]


def build_timeline(chapters_data):
    return [
        {'role': 'system', 'content': '你是一位故事分析师。根据各章节内容，提取剧情时间线事件。返回纯JSON数组（不要markdown代码块）：[{"chapter":1,"title":"章节标题","events":[{"event":"事件简述","detail":"详细描述","time_label":"时间标注"}]}]。每章提取1-3个关键事件。'},
        {'role': 'user', 'content': f'请提取以下作品的剧情时间线：\n\n{chapters_data}'}
    ]


def build_book_review(work_content):
    return [
        {'role': 'system', 'content': '你是一位资深文学评论家。请对提供的作品进行结构化书评，分为四个部分：1.亮点（作品的突出优点，1-2句话）；2.不足（可改进之处，1-2句话）；3.风格（写作风格分析，1-2句话）；4.推荐语（面向读者的推荐，1-2句话）。每个部分前用【亮点】【不足】【风格】【推荐语】作为标题。请用中文撰写，总计200-400字。'},
        {'role': 'user', 'content': f'请为以下作品撰写书评：\n\n{work_content}'}
    ]


def build_recommendation(profile_text):
    return [
        {'role': 'system', 'content': '你是一位阅读推荐专家。根据用户的阅读偏好和历史，为其推荐可能感兴趣的作品类型和主题标签。返回纯JSON对象（不要markdown代码块）：{"tags":["标签1","标签2","标签3"],"types":["novel","poetry"],"reason":"推荐理由简述"}。'},
        {'role': 'user', 'content': f'根据以下阅读偏好，推荐作品类型和标签：\n\n{profile_text}'}
    ]


def build_diagnose(content):
    return [
        {'role': 'system', 'content': (
            '你是一位资深文学编辑。请对用户的文字进行全面诊断，按以下维度分析：\n\n'
            '1. **总体评价**（1-2句话概括文字水平和特点）\n'
            '2. **节奏分析**（段落长短变化是否合理，有无拖沓或过快之处）\n'
            '3. **用词诊断**（是否有重复用词、不恰当的表达、可以替换的弱动词/形容词）\n'
            '4. **对话质量**（对话是否自然、是否能体现角色性格）\n'
            '5. **结构建议**（段落衔接是否顺畅、有无逻辑跳跃）\n'
            '6. **情感曲线**（情感起伏是否合理、高潮低谷分布）\n'
            '7. **改进建议**（列出 3-5 条具体可操作的修改建议，引用原文片段）\n\n'
            '请用中文撰写，结构清晰，每条建议要具体到可执行。'
        )},
        {'role': 'user', 'content': f'请诊断以下文字：\n\n{content}'}
    ]


def build_chat_system():
    return {
        'role': 'system',
        'content': (
            '你是墨池写作助手，一位创意写作伙伴。你的职责是：\n'
            '1. 和用户讨论故事创意、情节走向、角色发展\n'
            '2. 帮用户 brainstorm 灵感，提供写作建议\n'
            '3. 回答写作技巧相关的问题\n'
            '4. 当用户分享自己的想法时，积极回应并给出有建设性的拓展\n\n'
            '回复要求：简洁有温度，像一位懂创作的朋友在聊天。每次回复控制在300字以内。'
            '如果用户提供了故事片段，可以给出具体的修改建议或续写方向。'
        )
    }


def build_struct_review(chapters_summary, outline_text=None):
    """P4-E3b：第一轮结构审校 prompt（对照大纲审全书结构与节奏）。"""
    system = (
        '你是一位资深图书编辑，负责书籍的第一轮"结构审校"。请从结构与节奏层面诊断全书，'
        '不要逐句改文。'
    )
    user = '请对以下书稿做结构审校，输出：\n'
    user += '1. 【总体判断】1-2 句全书结构与节奏评价\n'
    user += '2. 【结构问题】列出：章节冗余/跑题/顺序不合理/篇幅失衡/与大纲脱节（有则写，无则写"无明显"）\n'
    user += '3. 【逐章建议】每章 1 句（如何取舍、承接、压缩或展开）\n'
    user += '4. 【优先级】给出最该先处理的三件事\n'
    user += '请用中文、条理清晰，控制在 600 字内。\n\n'
    if outline_text:
        user += f'=== 原定大纲（摘要）===\n{outline_text[:1200]}\n\n'
    user += '=== 当前章节（章名 + 字数 + 开头节选）===\n' + chapters_summary[:12000]
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]


def build_summary(chapter_title, chapter_content):
    """生成章节摘要的 prompt"""
    return [
        {'role': 'system', 'content': (
            '你是一位文学编辑。请为以下章节生成简洁的摘要，要求：\n'
            '1. 概括章节的主要情节和关键事件\n'
            '2. 提及重要角色和他们的行动\n'
            '3. 如果有重要的对话或冲突，简要说明\n'
            '4. 控制在 100-200 字\n'
            '5. 用中文撰写，语言流畅自然'
        )},
        {'role': 'user', 'content': f'章节标题：{chapter_title}\n\n章节内容：\n{chapter_content[:5000]}'}
    ]


def build_rp_extract(work_content):
    return [
        {'role': 'system', 'content': (
            '你是一位文学分析师。从作品文本中提取主要角色设定。'
            '对每个角色返回以下信息，用 JSON 数组格式（不要 markdown 代码块）：\n'
            '[{"name":"角色名","description":"一句话外貌描述","personality":"性格特点","background":"背景故事简述","speaking_style":"说话风格/口头禅"}]\n'
            '只提取有台词或重要戏份的角色，最多 8 个。'
        )},
        {'role': 'user', 'content': f'请从以下作品中提取角色设定：\n\n{work_content[:8000]}'}
    ]


def build_rp_chat(character, history, user_msg):
    char_info = (
        f'角色名：{character["name"]}\n'
        f'外貌：{character.get("description", "未知")}\n'
        f'性格：{character.get("personality", "未知")}\n'
        f'背景：{character.get("background", "未知")}\n'
        f'说话风格：{character.get("speaking_style", "自然")}'
    )
    return [
        {'role': 'system', 'content': (
            f'你现在要扮演以下角色与用户对话。严格保持角色性格和说话风格，不要跳出角色。\n\n'
            f'=== 角色设定 ===\n{char_info}\n=== end ===\n\n'
            '规则：\n'
            '1. 始终以该角色的第一人称说话\n'
            '2. 回复要符合角色性格和说话风格\n'
            '3. 每次回复控制在 200 字以内\n'
            '4. 可以引用作品中的情节，但不要剧透后续发展\n'
            '5. 用中文回复'
        )},
        *history[-20:],
        {'role': 'user', 'content': user_msg}
    ]


def build_mainline(inspiration, requirements=''):
    """二期：从灵感/闪念生成整体主线大方向（谁+想要什么+拦着什么→目标与冲突弧）。"""
    system = (
        '你是一位资深故事架构师。用户会给你一些故事灵感（可能零散）。'
        '请把它们整合为一条清晰的整体主线（Mainline）：'
        '包含【核心命题】【主角】【核心目标】【核心障碍】【冲突弧概览】【预期结局与主题】六项。'
        '语言精炼，每项 1-3 句，不做具体章节规划。'
    )
    user = f'灵感素材：\n{inspiration}'
    if requirements:
        user += f'\n\n用户补充要求：\n{requirements}'
    user += '\n\n请输出整体主线。'
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]


def build_volume_outline(mainline, volume_count=3):
    """二期：依据主线生成卷级故事曲线草稿（每卷 2-4 句目标/转折/走向）。"""
    system = (
        '你是一位资深故事架构师。根据用户给出的整体主线，生成卷级（Volumes）故事大纲草稿：'
        '分若干卷，每卷包含【卷目标】【主要转折】【结尾钩子】。'
        '卷级即可，不做章节级细化（章节到时边写边细化）。'
    )
    try:
        count = max(2, min(int(volume_count), 6))
    except (TypeError, ValueError):
        count = 3
    user = f'整体主线：\n{mainline}\n\n请分为 {count} 卷输出。'
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]


def build_chapter_plot(context, inspire_text, mainline='', chapter_no=0):
    """二期：任务卡 AI 生成本章剧情要点（结合前情/设定/主线/灵感）。"""
    system = (
        '你是一位帮写作者推进进度的编辑。根据作品上下文与灵感，生成本章（第 N 章）的剧情要点：'
        '包含【本章目标】【本章 Beats（3-6 条）】【本章钩子】【写完后建议提取的前情要点】。'
        'Beats 是具体情节步骤，不是抽象主题。'
    )
    user = f'作品上下文：\n{context}'
    if mainline:
        user += f'\n\n整体主线：\n{mainline}'
    if inspire_text:
        user += f'\n\n灵感素材：\n{inspire_text}'
    user += f'\n\n本章编号：第 {chapter_no} 章' if chapter_no else '\n\n本章编号：下一章'
    user += '\n\n请输出本章剧情要点。'
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]


def build_extract_points(chapter_content, chapter_title=''):
    """二期：用户写完一章后提取【本章要点】【本章钩子】【前情提要】。"""
    system = (
        '你是一位资深的编辑。给定一章已完成内容，提取三项供后续使用：'
        '【本章要点】（3-5 条核心事件）、【本章钩子】（结尾留下的悬念/期待）、'
        '【前情提要】（供下一章开头追述的一句话概述）。语言精炼。'
    )
    user = ''
    if chapter_title:
        user += f'章节标题：{chapter_title}\n\n'
    user += f'本章内容：\n{chapter_content[:12000]}\n\n请输出三项提取。'
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]


def build_unstick(context, chapter_content, last_summary=''):
    """二期：写作卡壳时，读本章实时内容 + 前几章摘要，生成"接下来写什么"。"""
    system = (
        '你是一位很有耐心的写作伙伴。用户写到这里卡住了。'
        '请基于本章已写内容与作品上下文，给出【接下来可以写什么】的具体建议 2-4 条：'
        '每条是一个可直接开写的情节方向（含承接上一段的衔接句示例）。'
        '不要说教，不要列抽象道理，给能直接接着写的料。'
    )
    user = f'作品上下文：\n{context}'
    if last_summary:
        user += f'\n\n前情摘要：\n{last_summary}'
    user += f'\n\n本章已写内容（截至卡壳处）：\n{chapter_content[:8000]}\n\n请给出接下来写什么的建议。'
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]
