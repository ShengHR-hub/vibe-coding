"""导入小说 TXT 到数据库（works + chapters 表）"""
import re
import sys
import os

# 让脚本可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import query, execute


def parse_novel(filepath, max_chapters=None):
    """解析 TXT 小说文件，返回 (meta, chapters)"""
    # 尝试多种编码（GBK 优先，小说 TXT 多为 GBK）
    for enc in ('gbk', 'gb18030', 'utf-8', 'utf-8-sig', 'gb2312', 'big5'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                lines = f.readlines()
            # 验证解码质量：检查前几行是否包含常见中文
            sample = ''.join(lines[:20])
            if any(c in sample for c in '的是在有不了人这中大为上个'):
                break
        except (UnicodeDecodeError, UnicodeError):
            continue
    else:
        raise RuntimeError(f'无法解码文件: {filepath}')

    # 提取元信息
    title = ''
    author = ''
    summary = ''
    content_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not title and ((stripped.startswith('《') and '》' in stripped) or stripped.startswith('书名：') or stripped.startswith('书名:')):
            title = stripped.replace('》', '').replace('《', '').replace('书名：', '').replace('书名:', '').strip()
        elif stripped.startswith('作者：') or stripped.startswith('作者:'):
            author = stripped.replace('作者：', '').replace('作者:', '').strip()
        elif stripped.startswith('内容简介') or stripped.startswith('简介'):
            # 后续几行是简介
            summary_lines = []
            for j in range(i + 1, min(i + 10, len(lines))):
                s = lines[j].strip()
                if s and not s.startswith('第') and '章' not in s[:5]:
                    summary_lines.append(s)
                else:
                    break
            summary = '\n'.join(summary_lines)

    # 按章节分割
    chapter_re = re.compile(r'^(第.{1,8}章\s*.+)')
    chapters = []
    current_title = None
    current_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        m = chapter_re.match(stripped)
        if m:
            # 保存上一章
            if current_title is not None:
                content = '\n'.join(current_lines).strip()
                # 去掉内容简介等非正文内容
                if content and '内容简介' not in current_title:
                    chapters.append({
                        'title': current_title,
                        'content': content,
                    })
            current_title = m.group(1).strip()
            current_lines = []
            # 检查是否达到上限
            if max_chapters and len(chapters) >= max_chapters:
                break
        elif current_title is not None:
            current_lines.append(line.rstrip())

    # 保存最后一章
    if current_title is not None and (not max_chapters or len(chapters) < max_chapters):
        content = '\n'.join(current_lines).strip()
        if content and '内容简介' not in current_title:
            chapters.append({
                'title': current_title,
                'content': content,
            })

    return {
        'title': title or '未命名作品',
        'author': author or '佚名',
        'summary': summary,
        'chapters': chapters,
    }


def import_to_db(novel, user_id=1, status='published', tags=''):
    """将解析后的小说导入数据库"""
    title = novel['title']
    summary = novel['summary']
    chapters = novel['chapters']

    # 计算总字数
    total_wc = sum(len(re.sub(r'\s', '', ch['content'])) for ch in chapters)

    # 插入作品
    work_id = execute(
        'INSERT INTO works (user_id, title, type, summary, tags, status, word_count) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s)',
        (user_id, title, 'novel', summary, tags, status, total_wc)
    )
    print(f'[OK] 作品已创建: {title} (work_id={work_id}, {len(chapters)}章, {total_wc}字)')

    # 插入章节
    for i, ch in enumerate(chapters, 1):
        wc = len(re.sub(r'\s', '', ch['content']))
        execute(
            'INSERT INTO chapters (work_id, chapter_no, title, content, word_count) '
            'VALUES (%s, %s, %s, %s, %s)',
            (work_id, i, ch['title'], ch['content'], wc)
        )
    print(f'[OK] {len(chapters)} 个章节已导入')

    return work_id


def main():
    import argparse
    parser = argparse.ArgumentParser(description='导入小说到墨池数据库')
    parser.add_argument('filepath', help='TXT 文件路径')
    parser.add_argument('--user-id', type=int, default=1, help='作者用户ID (默认1)')
    parser.add_argument('--max-chapters', type=int, default=None, help='最多导入章节数')
    parser.add_argument('--status', default='published', choices=['draft', 'published', 'private'])
    parser.add_argument('--tags', default='', help='标签，逗号分隔')
    parser.add_argument('--dry-run', action='store_true', help='仅解析不导入')
    args = parser.parse_args()

    if not os.path.exists(args.filepath):
        print(f'[ERR] 文件不存在: {args.filepath}')
        return

    print(f'正在解析: {args.filepath}')
    novel = parse_novel(args.filepath, max_chapters=args.max_chapters)
    print(f'标题: {novel["title"]}')
    print(f'作者: {novel["author"]}')
    print(f'简介: {novel["summary"][:100]}...' if len(novel['summary']) > 100 else f'简介: {novel["summary"]}')
    print(f'章节数: {len(novel["chapters"])}')
    total_chars = sum(len(ch['content']) for ch in novel['chapters'])
    print(f'总字符数: {total_chars:,}')

    if novel['chapters']:
        print(f'第一章: {novel["chapters"][0]["title"]} ({len(novel["chapters"][0]["content"]):,} 字符)')
        print(f'最后一章: {novel["chapters"][-1]["title"]} ({len(novel["chapters"][-1]["content"]):,} 字符)')

    if args.dry_run:
        print('\n[Dry Run] 未写入数据库')
        return

    work_id = import_to_db(novel, user_id=args.user_id, status=args.status, tags=args.tags)
    print(f'\n导入完成! work_id = {work_id}')
    print(f'访问: http://localhost:5173/works/{work_id}')


if __name__ == '__main__':
    main()
