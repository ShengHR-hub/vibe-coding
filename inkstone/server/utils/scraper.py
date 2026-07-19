"""
书籍爬虫工具 - 从外部网站抓取书籍数据入库
使用方法：python -m utils.scraper <url_or_keyword>
注意：部分网站使用 JavaScript 动态加载，爬虫可能无法获取完整内容
"""

import re
import sys
import requests
from bs4 import BeautifulSoup
from database.db import query, execute

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
}

# 支持的编码列表
ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']


def search_books(keyword, limit=10):
    """搜索书籍"""
    url = f'https://www.kxxs.top/search'
    try:
        resp = requests.get(url, params={'q': keyword}, headers=HEADERS, timeout=15)
        text = decode_response(resp)
        soup = BeautifulSoup(text, 'html.parser')

        results = []
        # 根据实际页面结构调整选择器
        book_items = soup.select('.book-item, .search-result-item, .book-info, .result-item, .book-list li')

        for item in book_items[:limit]:
            title_el = item.select_one('h3 a, .book-title a, .title a, a.title, a')
            author_el = item.select_one('.author, .book-author, .writer')

            if title_el:
                href = title_el.get('href', '')
                if href and not href.startswith('http'):
                    href = 'https://www.kxxs.top' + href
                results.append({
                    'title': title_el.get_text(strip=True),
                    'url': href,
                    'author': author_el.get_text(strip=True) if author_el else '未知',
                })

        print(f'搜索到 {len(results)} 个结果')
        return results
    except Exception as e:
        print(f'搜索失败: {e}')
        return []


def fetch_book_detail(url):
    """获取书籍详情"""
    try:
        if not url.startswith('http'):
            url = 'https://www.kxxs.top' + url

        resp = requests.get(url, headers=HEADERS, timeout=15)
        text = decode_response(resp)
        soup = BeautifulSoup(text, 'html.parser')

        # 根据实际页面结构调整
        title = soup.select_one('h1, .book-title, .book-name, .title, .info h1, .info h2')
        author = soup.select_one('.author, .book-author, .writer, .info .author')
        summary = soup.select_one('.summary, .book-summary, .intro, .description, .book-intro')
        cover = soup.select_one('.cover img, .book-cover img, .book-img img, .info img')
        type_el = soup.select_one('.type, .category, .tag, .book-type')

        book_info = {
            'title': title.get_text(strip=True) if title else '未知',
            'author': author.get_text(strip=True) if author else '未知',
            'summary': summary.get_text(strip=True)[:500] if summary else '',
            'cover_image': cover.get('src', '') if cover else '',
            'type': parse_type(type_el.get_text(strip=True) if type_el else ''),
        }

        # 获取章节列表 - 尝试多种选择器
        chapters = []
        chapter_selectors = [
            '.chapter-list a',
            '.catalog a',
            '.volume-list a',
            '.list-chapter a',
            '.book-list a',
            '#list a',
            '.chapter a',
            '.mulu a',
            'dl dd a',
        ]

        chapter_list = []
        for sel in chapter_selectors:
            chapter_list = soup.select(sel)
            if chapter_list and len(chapter_list) > 0:
                print(f'使用选择器 {sel} 找到 {len(chapter_list)} 个章节')
                break

        # 过滤掉非章节链接
        for ch in chapter_list:
            href = ch.get('href', '')
            title_text = ch.get_text(strip=True)
            # 跳过空链接或明显的导航链接
            if not href or href == '#' or not title_text:
                continue
            # 跳过太短的标题（可能是导航）
            if len(title_text) < 2:
                continue
            # 跳过明显的非章节链接
            if any(x in title_text.lower() for x in ['首页', '登录', '注册', '搜索', '排行']):
                continue
            chapters.append({
                'chapter_no': len(chapters) + 1,
                'title': title_text,
                'url': href,
            })

        book_info['chapters'] = chapters
        print(f'获取到 {len(chapters)} 个章节')
        return book_info

    except Exception as e:
        print(f'获取详情失败: {e}')
        return None


def decode_response(resp):
    """尝试多种编码解码响应内容"""
    # 先尝试响应头中的编码
    if resp.encoding and resp.encoding.lower() != 'iso-8859-1':
        try:
            return resp.content.decode(resp.encoding)
        except:
            pass

    # 尝试常见编码
    for encoding in ENCODINGS:
        try:
            text = resp.content.decode(encoding)
            # 检查是否包含中文字符
            if any('一' <= c <= '鿿' for c in text[:100]):
                return text
        except:
            continue

    # 最后用 utf-8 容错模式
    return resp.content.decode('utf-8', errors='replace')


def fetch_chapter_content(url):
    """获取章节内容"""
    try:
        if not url.startswith('http'):
            url = 'https://www.kxxs.top' + url

        resp = requests.get(url, headers=HEADERS, timeout=15)
        text = decode_response(resp)
        soup = BeautifulSoup(text, 'html.parser')

        # 尝试多种常见选择器
        selectors = [
            '.chapter-content',
            '.content',
            '#content',
            '.read-content',
            '.txt-content',
            '.article-content',
            '.book-content',
            'article',
            '.main-content',
            '.text-content',
            '.novel-content',
        ]

        content_el = None
        for sel in selectors:
            content_el = soup.select_one(sel)
            if content_el and len(content_el.get_text(strip=True)) > 50:
                break

        if content_el:
            # 清理内容
            for tag in content_el.select('script, style, .ads, .ad, .recommend, .bottom, .nav, .header'):
                tag.decompose()
            result = content_el.get_text(separator='\n', strip=True)
            if len(result) > 10:
                return result

        # 兜底：提取 body 中的长文本块
        body = soup.find('body')
        if body:
            for tag in body.select('script, style, nav, header, footer, .nav, .header, .footer, .sidebar'):
                tag.decompose()
            result = body.get_text(separator='\n', strip=True)
            # 只返回有意义的长文本
            if len(result) > 100:
                return result[:50000]  # 限制长度

        print(f'未找到内容，页面URL: {url}')
        print(f'页面标题: {soup.title.string if soup.title else "无"}')
        return ''

    except Exception as e:
        print(f'获取章节内容失败: {e}')
        return ''


def parse_type(type_str):
    """解析书籍类型"""
    type_map = {
        '小说': 'novel', '玄幻': 'novel', '都市': 'novel', '仙侠': 'novel',
        '诗歌': 'poetry', '诗词': 'poetry',
        '散文': 'essay', '随笔': 'essay',
        '网文': 'webfiction', '网络小说': 'webfiction',
    }
    for k, v in type_map.items():
        if k in type_str:
            return v
    return 'novel'


def import_book(book_info, uploader_id=None):
    """将书籍导入数据库"""
    title = book_info['title']
    author = book_info['author']

    # 检查是否已存在
    existing = query(
        'SELECT book_id FROM library_books WHERE title = %s AND author = %s',
        (title, author), one=True
    )
    if existing:
        print(f'书籍《{title}》已存在 (ID: {existing["book_id"]})')
        return existing['book_id']

    # 计算字数
    total_words = 0
    chapters = book_info.get('chapters', [])

    # 插入书籍
    book_id = execute(
        'INSERT INTO library_books (title, author, summary, cover_image, type, word_count, chapter_count, uploader_id, source) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (title, author, book_info.get('summary', ''), book_info.get('cover_image', ''),
         book_info.get('type', 'novel'), total_words, len(chapters), uploader_id, 'crawler')
    )

    print(f'已导入《{title}》(ID: {book_id})，{len(chapters)} 章')

    # 导入章节
    for ch in chapters:
        content = ''
        if ch.get('url'):
            print(f'  获取第{ch["chapter_no"]}章: {ch["title"]}...')
            content = fetch_chapter_content(ch['url'])

        word_count = len(content)
        total_words += word_count

        execute(
            'INSERT INTO library_chapters (book_id, chapter_no, title, content, word_count) VALUES (%s, %s, %s, %s, %s)',
            (book_id, ch['chapter_no'], ch['title'], content, word_count)
        )

    # 更新总字数
    execute('UPDATE library_books SET word_count = %s WHERE book_id = %s', (total_words, book_id))

    print(f'导入完成，总字数: {total_words}')
    return book_id


def main():
    if len(sys.argv) < 2:
        print('用法: python -m utils.scraper <搜索关键词或URL>')
        print('示例: python -m utils.scraper 三体')
        return

    target = sys.argv[1]

    if target.startswith('http'):
        # 直接抓取指定URL
        print(f'正在获取: {target}')
        book_info = fetch_book_detail(target)
        if book_info:
            import_book(book_info)
        else:
            print('获取失败')
    else:
        # 搜索关键词
        print(f'搜索: {target}')
        results = search_books(target)
        if not results:
            print('未找到结果')
            return

        print(f'找到 {len(results)} 个结果:')
        for i, r in enumerate(results, 1):
            print(f'  {i}. {r["title"]} - {r["author"]}')

        # 导入第一个结果
        choice = input('\n输入序号导入 (直接回车导入第1个，输入0取消): ').strip()
        if choice == '0':
            return

        idx = int(choice) - 1 if choice else 0
        if 0 <= idx < len(results):
            book_info = fetch_book_detail(results[idx]['url'])
            if book_info:
                import_book(book_info)


if __name__ == '__main__':
    main()
