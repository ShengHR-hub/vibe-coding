"""补充作品内容，让种子数据更真实"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import query, execute
from utils.mimos import chat_completion


def get_works_to_enrich():
    """获取需要补充内容的作品"""
    return query('''
        SELECT w.work_id, w.title, w.type, w.summary, w.word_count,
               c.chapter_id, c.title as chapter_title, c.content
        FROM works w
        JOIN chapters c ON w.work_id = c.work_id
        WHERE w.word_count < 500
        ORDER BY w.work_id
    ''')


def generate_content(work):
    """使用 AI 生成作品内容"""
    title = work['title']
    work_type = work['type']
    summary = work.get('summary', '')

    # 根据作品类型生成不同的 prompt
    type_prompts = {
        'novel': f'你是一位小说家。请为小说《{title}》的第一章创作内容。',
        'poetry': f'你是一位诗人。请为诗集《{title}》创作几首诗。',
        'essay': f'你是一位散文家。请为散文集《{title}》创作一篇散文。',
        'script': f'你是一位剧作家。请为剧本《{title}》创作第一幕。',
    }

    prompt = type_prompts.get(work_type, type_prompts['novel'])

    if summary:
        prompt += f'\n\n简介：{summary}'

    prompt += '\n\n要求：'
    prompt += '\n- 内容要符合中文写作规范'
    prompt += '\n- 语言优美，有文学性'
    prompt += '\n- 字数控制在 800-1500 字'
    prompt += '\n- 直接输出内容，不要加标题或说明'

    messages = [
        {'role': 'system', 'content': '你是一位专业的中文作家，擅长创作高质量的文学作品。请用中文创作。'},
        {'role': 'user', 'content': prompt}
    ]

    try:
        result = chat_completion(messages, temperature=0.8, max_tokens=2000)
        return result
    except Exception as e:
        print(f'  [ERROR] AI 生成失败: {e}')
        return None


def enrich_works():
    """补充作品内容"""
    works = get_works_to_enrich()

    if not works:
        print('没有需要补充的作品')
        return

    print(f'找到 {len(works)} 个需要补充的作品')

    for work in works:
        work_id = work['work_id']
        title = work['title']
        current_wc = work['word_count']

        print(f'\n处理: {title} (ID:{work_id}, 当前{current_wc}字)')

        # 生成新内容
        new_content = generate_content(work)
        if not new_content:
            continue

        # 计算字数
        new_wc = len(new_content.replace(' ', '').replace('\n', ''))

        # 更新章节内容
        execute(
            'UPDATE chapters SET content = %s, word_count = %s WHERE chapter_id = %s',
            (new_content, new_wc, work['chapter_id'])
        )

        # 更新作品总字数
        total_wc = query(
            'SELECT COALESCE(SUM(word_count), 0) as wc FROM chapters WHERE work_id = %s',
            (work_id,), one=True
        )['wc']
        execute(
            'UPDATE works SET word_count = %s WHERE work_id = %s',
            (total_wc, work_id)
        )

        print(f'  [OK] 已更新: {current_wc}字 -> {total_wc}字')


if __name__ == '__main__':
    enrich_works()
