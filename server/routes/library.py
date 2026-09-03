import re
import os
import uuid
from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, _fmt, login_required

library_bp = Blueprint('library', __name__)


@library_bp.get('')
def book_list():
    """书库列表：合并 works(published) + library_books"""
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(30, request.args.get('page_size', 12, type=int))
    book_type = request.args.get('type', '')
    sort = request.args.get('sort', 'hot')
    tag = request.args.get('tag', '')

    # 构建 works 查询
    works_where = ["w.status = 'published'"]
    works_params = []
    if book_type:
        works_where.append('w.type = %s')
        works_params.append(book_type)
    if tag:
        works_where.append('w.tags LIKE %s')
        works_params.append(f'%{tag}%')
    works_cond = ' AND '.join(works_where)

    works_sql = f'''
        SELECT w.work_id as book_id, w.title, u.author, w.summary, w.cover_image,
               w.type, w.tags, w.word_count, 0 as chapter_count,
               w.views, w.favorites_count, 0 as rating_avg, 0 as rating_count,
               w.created_at, w.updated_at, 'work' as source, w.user_id as owner_id
        FROM works w
        LEFT JOIN (SELECT user_id, username as author FROM users) u ON w.user_id = u.user_id
        WHERE {works_cond}
    '''

    # 构建 library_books 查询
    lib_where = ['1=1']
    lib_params = []
    if book_type:
        lib_where.append('lb.type = %s')
        lib_params.append(book_type)
    if tag:
        lib_where.append('lb.tags LIKE %s')
        lib_params.append(f'%{tag}%')
    lib_cond = ' AND '.join(lib_where)

    lib_sql = f'''
        SELECT lb.book_id, lb.title, lb.author, lb.summary, lb.cover_image,
               lb.type, lb.tags, lb.word_count, lb.chapter_count,
               lb.views, lb.favorites_count, lb.rating_avg, lb.rating_count,
               lb.created_at, lb.updated_at, 'library' as source, lb.uploader_id as owner_id
        FROM library_books lb
        WHERE {lib_cond}
    '''

    # 排序
    if sort == 'hot':
        order = 'ORDER BY (views + favorites_count * 5) DESC, created_at DESC'
    elif sort == 'new':
        order = 'ORDER BY created_at DESC'
    elif sort == 'rating':
        order = 'ORDER BY rating_avg DESC, rating_count DESC'
    else:
        order = 'ORDER BY created_at DESC'

    # 合并查询
    all_sql = f'({works_sql}) UNION ALL ({lib_sql}) {order}'
    all_params = works_params + lib_params

    # 总数
    count_sql = f'SELECT COUNT(*) as cnt FROM ({all_sql}) t'
    total = query(count_sql, all_params, one=True)['cnt']

    # 分页
    rows = query(f'{all_sql} LIMIT %s OFFSET %s', all_params + [page_size, (page - 1) * page_size])

    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))
        r['updated_at'] = _fmt(r.get('updated_at'))

    return ok({'items': rows, 'total': total, 'page': page, 'page_size': page_size})


@library_bp.get('/search')
def search():
    """全文搜索"""
    q = (request.args.get('q') or '').strip()
    book_type = request.args.get('type', '')
    sort = request.args.get('sort', 'relevance')
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(30, request.args.get('page_size', 12, type=int))

    if not q:
        return fail('请输入搜索关键词')

    like_q = f'%{q}%'

    # 搜索 works
    works_where = ["w.status = 'published'", '(w.title LIKE %s OR w.summary LIKE %s)']
    works_params = [like_q, like_q]
    if book_type:
        works_where.append('w.type = %s')
        works_params.append(book_type)
    works_cond = ' AND '.join(works_where)

    works_sql = f'''
        SELECT w.work_id as book_id, w.title, u.author, w.summary, w.cover_image,
               w.type, w.tags, w.word_count, 0 as chapter_count,
               w.views, w.favorites_count, 0 as rating_avg, 0 as rating_count,
               w.created_at, w.updated_at, 'work' as source
        FROM works w
        LEFT JOIN (SELECT user_id, username as author FROM users) u ON w.user_id = u.user_id
        WHERE {works_cond}
    '''

    # 搜索 library_books
    lib_where = ['(lb.title LIKE %s OR lb.summary LIKE %s OR lb.author LIKE %s)']
    lib_params = [like_q, like_q, like_q]
    if book_type:
        lib_where.append('lb.type = %s')
        lib_params.append(book_type)
    lib_cond = ' AND '.join(lib_where)

    lib_sql = f'''
        SELECT lb.book_id, lb.title, lb.author, lb.summary, lb.cover_image,
               lb.type, lb.tags, lb.word_count, lb.chapter_count,
               lb.views, lb.favorites_count, lb.rating_avg, lb.rating_count,
               lb.created_at, lb.updated_at, 'library' as source
        FROM library_books lb
        WHERE {lib_cond}
    '''

    all_sql = f'({works_sql}) UNION ALL ({lib_sql}) ORDER BY created_at DESC'
    all_params = works_params + lib_params

    total = query(f'SELECT COUNT(*) as cnt FROM ({all_sql}) t', all_params, one=True)['cnt']
    rows = query(f'{all_sql} LIMIT %s OFFSET %s', all_params + [page_size, (page - 1) * page_size])

    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))
        r['updated_at'] = _fmt(r.get('updated_at'))

    return ok({'items': rows, 'total': total, 'page': page, 'page_size': page_size})


@library_bp.delete('/<int:book_id>')
@login_required
def delete_book(book_id):
    """删除书籍（仅限所有者）"""
    source = request.args.get('source', 'library')
    user_id = session['user_id']

    if source == 'work':
        work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s',
                      (book_id, user_id), one=True)
        if not work:
            return fail('作品不存在或无权删除', code=404)
        execute('DELETE FROM works WHERE work_id = %s', (book_id,))
        return ok(msg='作品已删除')
    else:
        book = query('SELECT book_id FROM library_books WHERE book_id = %s AND uploader_id = %s',
                      (book_id, user_id), one=True)
        if not book:
            return fail('书籍不存在或无权删除', code=404)
        execute('DELETE FROM library_books WHERE book_id = %s', (book_id,))
        return ok(msg='书籍已删除')


@library_bp.get('/recommend')
@login_required
def recommend():
    """基于阅读偏好推荐书籍"""
    user_id = session.get('user_id')
    limit = min(20, request.args.get('limit', 6, type=int))

    # 分析用户阅读类型偏好
    type_pref = query('''
        SELECT CASE rp.book_type
          WHEN 'library' THEN (SELECT type FROM library_books WHERE book_id = rp.book_id)
          WHEN 'work' THEN (SELECT type FROM works WHERE work_id = rp.book_id)
        END as book_type, COUNT(*) as cnt
        FROM reading_progress rp
        WHERE rp.user_id = %s
        GROUP BY book_type
        ORDER BY cnt DESC
        LIMIT 3
    ''', (user_id,))

    if not type_pref:
        # 无阅读记录，返回热门书籍
        rows = query('''
            SELECT book_id, title, author, type, rating_avg, views, 'library' as source
            FROM library_books
            ORDER BY (views + favorites_count * 5) DESC
            LIMIT %s
        ''', (limit,))
        return ok({'items': rows, 'preference': None})

    # 获取用户已读书籍 ID
    read_books = query(
        'SELECT book_id, book_type FROM reading_progress WHERE user_id = %s',
        (user_id,)
    )
    read_ids = set((r['book_id'], r['book_type']) for r in read_books)

    preferred_types = [t['book_type'] for t in type_pref if t['book_type']]

    # 推荐同类型热门书籍（排除已读）
    recommendations = []
    for ptype in preferred_types:
        if not ptype:
            continue
        books = query('''
            SELECT book_id, title, author, type, rating_avg, views, 'library' as source
            FROM library_books
            WHERE type = %s
            ORDER BY (views + favorites_count * 5) DESC
            LIMIT %s
        ''', (ptype, limit))
        for b in books:
            if (b['book_id'], 'library') not in read_ids:
                recommendations.append(b)

    # 补充不足的推荐
    if len(recommendations) < limit:
        extra = query('''
            SELECT book_id, title, author, type, rating_avg, views, 'library' as source
            FROM library_books
            ORDER BY (views + favorites_count * 5) DESC
            LIMIT %s
        ''', (limit * 2,))
        for b in extra:
            if len(recommendations) >= limit:
                break
            if (b['book_id'], 'library') not in read_ids and b not in recommendations:
                recommendations.append(b)

    return ok({
        'items': recommendations[:limit],
        'preference': [{'type': t['book_type'], 'count': t['cnt']} for t in type_pref if t['book_type']],
    })


@library_bp.post('/import')
@login_required
def import_from_url():
    """从URL导入书籍"""
    import re
    from urllib.parse import urlparse

    user_id = session.get('user_id')
    data = request.get_json(force=True)
    url = data.get('url', '').strip()

    if not url:
        return fail('请输入书籍URL')

    # SSRF 防护：只允许 http/https，禁止内网地址
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        return fail('仅支持 http/https 协议')
    hostname = parsed.hostname or ''
    if hostname in ('localhost', '127.0.0.1', '0.0.0.0', '::1') or \
       re.match(r'^(10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.)', hostname):
        return fail('不允许访问内网地址')

    from utils.scraper import fetch_book_detail, import_book

    book_info = fetch_book_detail(url)
    if not book_info:
        return fail('获取书籍信息失败')

    book_id = import_book(book_info, uploader_id=user_id)
    return ok({'book_id': book_id, 'title': book_info['title']})


@library_bp.get('/search-external')
@login_required
def search_external():
    """搜索外部书籍"""
    keyword = request.args.get('q', '').strip()
    if not keyword:
        return fail('请输入搜索关键词')

    from utils.scraper import search_books
    results = search_books(keyword, limit=10)
    return ok({'items': results})


@library_bp.get('/categories')
def categories():
    """分类标签列表"""
    # 从 works 和 library_books 中提取所有去重标签
    works_tags = query("SELECT tags FROM works WHERE status = 'published' AND tags != ''")
    lib_tags = query("SELECT tags FROM library_books WHERE tags != ''")

    all_tags = set()
    for row in works_tags + lib_tags:
        for t in row['tags'].split(','):
            t = t.strip()
            if t:
                all_tags.add(t)

    # 类型列表
    types = [
        {'value': 'novel', 'label': '小说'},
        {'value': 'essay', 'label': '散文'},
        {'value': 'poetry', 'label': '诗歌'},
        {'value': 'webfiction', 'label': '网文'},
    ]

    return ok({'tags': sorted(all_tags), 'types': types})


@library_bp.get('/rankings')
def rankings():
    """排行榜"""
    sort = request.args.get('sort', 'hot')
    limit = min(20, request.args.get('limit', 10, type=int))

    lib_order_map = {
        'hot': '(views + favorites_count * 5) DESC',
        'rating': 'rating_avg DESC, rating_count DESC',
        'new': 'created_at DESC',
    }
    works_order_map = {
        'hot': '(views + favorites_count * 5) DESC',
        'rating': '0 DESC, 0 DESC',
        'new': 'created_at DESC',
    }
    lib_order = lib_order_map.get(sort, lib_order_map['hot'])
    works_order = works_order_map.get(sort, works_order_map['hot'])

    # 从 library_books 取排行
    lib_rows = query(f'''
        SELECT book_id, title, author, cover_image, type, word_count,
               views, favorites_count, rating_avg, rating_count,
               created_at, 'library' as source
        FROM library_books
        ORDER BY {lib_order}
        LIMIT %s
    ''', (limit,))

    # 从 works 取排行
    works_rows = query(f'''
        SELECT w.work_id as book_id, w.title, u.author, w.cover_image, w.type, w.word_count,
               w.views, w.favorites_count, 0 as rating_avg, 0 as rating_count,
               w.created_at, 'work' as source
        FROM works w
        LEFT JOIN (SELECT user_id, username as author FROM users) u ON w.user_id = u.user_id
        WHERE w.status = 'published'
        ORDER BY {works_order}
        LIMIT %s
    ''', (limit,))

    for r in lib_rows + works_rows:
        r['created_at'] = _fmt(r.get('created_at'))

    return ok({'library': lib_rows, 'works': works_rows})


@library_bp.get('/featured')
def featured():
    """精选推荐"""
    # 热门前 6 本（合并两个来源）
    lib_rows = query('''
        SELECT book_id, title, author, summary, cover_image, type, word_count,
               views, rating_avg, 'library' as source
        FROM library_books
        ORDER BY (views + favorites_count * 5) DESC
        LIMIT 6
    ''')

    works_rows = query('''
        SELECT w.work_id as book_id, w.title, u.author, w.summary, w.cover_image, w.type, w.word_count,
               w.views, 0 as rating_avg, 'work' as source
        FROM works w
        LEFT JOIN (SELECT user_id, username as author FROM users) u ON w.user_id = u.user_id
        WHERE w.status = 'published'
        ORDER BY (w.views + w.favorites_count * 5) DESC
        LIMIT 6
    ''')

    # 合并取前 6
    combined = lib_rows + works_rows
    combined.sort(key=lambda x: (x.get('views', 0) or 0), reverse=True)

    return ok({'items': combined[:6]})


@library_bp.get('/<int:book_id>')
def book_detail(book_id):
    """书籍详情"""
    source = request.args.get('source', 'library')

    if source == 'work':
        row = query('''
            SELECT w.*, u.username, u.avatar, u.level
            FROM works w
            LEFT JOIN users u ON w.user_id = u.user_id
            WHERE w.work_id = %s AND w.status = 'published'
        ''', (book_id,), one=True)
        if not row:
            return fail('作品不存在', code=404)
        row['source'] = 'work'
        row['author'] = row.get('username', '')
        # 获取章节目录
        chapters = query(
            'SELECT chapter_id, chapter_no, title, word_count FROM chapters WHERE work_id = %s ORDER BY chapter_no',
            (book_id,)
        )
        # 获取卷
        volumes = query(
            'SELECT volume_id, volume_no, title FROM volumes WHERE work_id = %s ORDER BY volume_no',
            (book_id,)
        )
    else:
        row = query('SELECT * FROM library_books WHERE book_id = %s', (book_id,), one=True)
        if not row:
            return fail('书籍不存在', code=404)
        row['source'] = 'library'
        chapters = query(
            'SELECT chapter_id, chapter_no, title, word_count, content FROM library_chapters WHERE book_id = %s ORDER BY chapter_no',
            (book_id,)
        )
        volumes = query(
            'SELECT volume_id, volume_no, title FROM library_volumes WHERE book_id = %s ORDER BY volume_no',
            (book_id,)
        )

    row['created_at'] = _fmt(row.get('created_at'))
    row['updated_at'] = _fmt(row.get('updated_at'))

    # 增加阅读量（仅书库书籍，作品由 /api/works/public 已处理）
    if source != 'work':
        execute('UPDATE library_books SET views = views + 1 WHERE book_id = %s', (book_id,))

    # 检查用户是否在书架
    on_shelf = False
    shelf_id = None
    user_id = session.get('user_id')
    if user_id:
        shelf = query(
            'SELECT shelf_id FROM reading_bookshelf WHERE user_id = %s AND book_type = %s AND book_id = %s',
            (user_id, source, book_id), one=True
        )
        if shelf:
            on_shelf = True
            shelf_id = shelf['shelf_id']

    return ok({
        'book': row,
        'chapters': chapters,
        'volumes': volumes,
        'on_shelf': on_shelf,
        'shelf_id': shelf_id,
    })


@library_bp.get('/<int:book_id>/chapters')
def chapter_list(book_id):
    """章节列表"""
    source = request.args.get('source', 'library')

    if source == 'work':
        chapters = query(
            'SELECT chapter_id, chapter_no, title, word_count, volume_id FROM chapters WHERE work_id = %s ORDER BY chapter_no',
            (book_id,)
        )
    else:
        chapters = query(
            'SELECT chapter_id, chapter_no, title, word_count, volume_id FROM library_chapters WHERE book_id = %s ORDER BY chapter_no',
            (book_id,)
        )

    return ok({'chapters': chapters})


@library_bp.get('/<int:book_id>/chapters/<int:chapter_id>')
def chapter_content(book_id, chapter_id):
    """章节内容"""
    source = request.args.get('source', 'library')

    if source == 'work':
        ch = query(
            'SELECT * FROM chapters WHERE chapter_id = %s AND work_id = %s',
            (chapter_id, book_id), one=True
        )
    else:
        ch = query(
            'SELECT * FROM library_chapters WHERE chapter_id = %s AND book_id = %s',
            (chapter_id, book_id), one=True
        )

    if not ch:
        return fail('章节不存在', code=404)

    ch['created_at'] = _fmt(ch.get('created_at'))
    return ok({'chapter': ch})


def _detect_encoding(filepath):
    """检测文件编码：尝试常见编码，返回第一个能完整解码的"""
    # UTF-8 BOM 优先
    with open(filepath, 'rb') as f:
        head = f.read(4)
    if head[:3] == b'\xef\xbb\xbf':
        return 'utf-8-sig'

    for enc in ('utf-8', 'gbk', 'gb18030', 'gb2312', 'big5', 'shift_jis'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                f.read(4000)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None


def _parse_txt(filepath, filename=None):
    """解析 TXT 文件，提取元信息和章节"""
    enc = _detect_encoding(filepath)
    if not enc:
        raise RuntimeError(f'无法解码文件: {filepath}')

    with open(filepath, 'r', encoding=enc) as f:
        lines = f.readlines()

    title = ''
    author = ''
    summary = ''

    # 优先从文件名提取标题和作者
    if filename:
        name = filename.replace('.txt', '').replace('.TXT', '')
        # 格式: 《书名》作者：作者名 或 《书名》（备注）作者：作者名
        title_match = re.search(r'《(.+?)》', name)
        if title_match:
            title = title_match.group(1).strip()
        author_match = re.search(r'作者[：:](.+?)(?:\s|$|[（(])', name)
        if author_match:
            author = author_match.group(1).strip()

    # 从文件内容补充信息
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not title and ((stripped.startswith('《') and '》' in stripped) or
                          stripped.startswith('书名：') or stripped.startswith('书名:')):
            title = stripped.replace('》', '').replace('《', '').replace('书名：', '').replace('书名:', '').strip()
        if not author and (stripped.startswith('作者：') or stripped.startswith('作者:')):
            author = stripped.replace('作者：', '').replace('作者:', '').strip()
        if not summary and (stripped.startswith('内容简介') or stripped.startswith('简介')):
            summary_lines = []
            for j in range(i + 1, min(i + 10, len(lines))):
                s = lines[j].strip()
                if s and not s.startswith('第') and '章' not in s[:5]:
                    summary_lines.append(s)
                else:
                    break
            summary = '\n'.join(summary_lines)

    chapter_re = re.compile(r'^(第.{1,10}[章节回卷集篇]\s*.+|楔子\s*.*|序[章幕]\s*.*|尾声\s*.*|引[子言]\s*.*|番外\s*.+|终章\s*.*)')
    chapters = []
    current_title = None
    current_lines = []

    for line in lines:
        stripped = line.strip()
        m = chapter_re.match(stripped)
        if m:
            if current_title is not None:
                content = '\n'.join(current_lines).strip()
                if content and '内容简介' not in current_title:
                    chapters.append({'title': current_title, 'content': content})
            current_title = m.group(1).strip()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line.rstrip())

    if current_title is not None:
        content = '\n'.join(current_lines).strip()
        if content and '内容简介' not in current_title:
            chapters.append({'title': current_title, 'content': content})

    return {
        'title': title or '未命名作品',
        'author': author or '佚名',
        'summary': summary,
        'chapters': chapters,
    }


@library_bp.post('/upload')
@login_required
def upload():
    """用户上传 TXT 文件"""
    file = request.files.get('file')
    if not file or not file.filename:
        return fail('请上传文件')

    if not file.filename.lower().endswith('.txt'):
        return fail('仅支持 TXT 格式')

    # 检查文件大小（最大 10MB）
    file_bytes = file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        return fail('文件过大，最大允许 10MB')

    # 保存临时文件（使用安全文件名防止路径穿越）
    from werkzeug.utils import secure_filename
    tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads', 'tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    safe_name = secure_filename(file.filename) or f'{uuid.uuid4().hex}.txt'
    tmp_path = os.path.join(tmp_dir, safe_name)
    with open(tmp_path, 'wb') as f:
        f.write(file_bytes)

    try:
        novel = _parse_txt(tmp_path, filename=file.filename)
    except RuntimeError as e:
        os.remove(tmp_path)
        return fail(str(e))
    except Exception as e:
        os.remove(tmp_path)
        return fail(f'解析失败: {str(e)}')

    if not novel['chapters']:
        os.remove(tmp_path)
        return fail('未识别到任何章节，请检查文件格式')

    # 覆盖前端传入的元信息
    title = request.form.get('title', '').strip() or novel['title']
    author = request.form.get('author', '').strip() or novel['author']
    book_type = request.form.get('type', 'novel').strip()

    novel['title'] = title
    novel['author'] = author

    # 去重
    existing = query(
        'SELECT book_id FROM library_books WHERE title = %s AND author = %s',
        (title, author)
    )
    if existing:
        os.remove(tmp_path)
        return fail(f'书籍已存在 (book_id={existing[0]["book_id"]})')

    # 计算字数
    total_wc = sum(len(re.sub(r'\s', '', ch['content'])) for ch in novel['chapters'])

    # 插入
    user_id = session.get('user_id')
    book_id = execute(
        'INSERT INTO library_books (title, author, summary, type, word_count, chapter_count, source, uploader_id) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
        (title, author, novel['summary'], book_type, total_wc, len(novel['chapters']), 'user_upload', user_id)
    )

    for i, ch in enumerate(novel['chapters'], 1):
        wc = len(re.sub(r'\s', '', ch['content']))
        execute(
            'INSERT INTO library_chapters (book_id, chapter_no, title, content, word_count) '
            'VALUES (%s, %s, %s, %s, %s)',
            (book_id, i, ch['title'], ch['content'], wc)
        )

    os.remove(tmp_path)

    return ok({'book_id': book_id, 'title': title, 'chapters': len(novel['chapters']), 'word_count': total_wc})
