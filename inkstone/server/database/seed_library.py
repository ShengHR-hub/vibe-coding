"""导入本地 TXT 小说到书库（library_books + library_chapters）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import query
from database.import_novel import parse_novel, import_to_library


NOVELS = [
    {
        'path': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                             '1153', '《仙逆》（校对版全本）作者：耳根.txt'),
        'tags': '仙侠,修真,耳根',
        'book_type': 'webfiction',
        'max_chapters': 50,
    },
    {
        'path': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                             '《剑来》 作者：烽火戏诸侯', '《剑来》 作者：烽火戏诸侯.txt'),
        'tags': '仙侠,烽火戏诸侯,剑来',
        'book_type': 'webfiction',
        'max_chapters': 50,
    },
]


def seed_library_books():
    """导入小说到书库"""
    for novel_info in NOVELS:
        filepath = novel_info['path']
        if not os.path.exists(filepath):
            print(f'[SKIP] 文件不存在: {filepath}')
            continue

        # 检查是否已导入
        novel = parse_novel(filepath, max_chapters=novel_info['max_chapters'])
        existing = query(
            'SELECT book_id FROM library_books WHERE title = %s AND author = %s',
            (novel['title'], novel['author'])
        )
        if existing:
            print(f'[SKIP] 已存在: {novel["title"]} (book_id={existing[0]["book_id"]})')
            continue

        book_id = import_to_library(
            novel,
            book_type=novel_info['book_type'],
            tags=novel_info['tags'],
            source='seed_import',
        )
        print(f'[OK] 导入成功: {novel["title"]} → book_id={book_id}')


if __name__ == '__main__':
    seed_library_books()
