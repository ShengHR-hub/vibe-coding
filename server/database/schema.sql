-- 墨池 Inkstone 数据库建表脚本
-- MySQL 8.0+

CREATE DATABASE IF NOT EXISTS inkstone CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE inkstone;

-- 1. 用户表
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    avatar VARCHAR(500) DEFAULT '',
    cover_image VARCHAR(500) DEFAULT '',
    bio VARCHAR(500) DEFAULT '',
    level INT DEFAULT 1,
    exp INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 作品表
CREATE TABLE works (
    work_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    type ENUM('novel', 'poetry', 'essay', 'script') NOT NULL DEFAULT 'novel',
    summary TEXT,
    cover_image VARCHAR(500) DEFAULT '',
    tags VARCHAR(500) DEFAULT '',
    status ENUM('draft', 'published', 'private') DEFAULT 'draft',
    serialization_status ENUM('serializing', 'completed', 'paused') DEFAULT 'serializing',
    views INT DEFAULT 0,
    likes_count INT DEFAULT 0,
    comments_count INT DEFAULT 0,
    favorites_count INT DEFAULT 0,
    word_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_works_user (user_id),
    INDEX idx_works_type (type),
    INDEX idx_works_status (status),
    INDEX idx_works_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 章节表
CREATE TABLE chapters (
    chapter_id INT AUTO_INCREMENT PRIMARY KEY,
    work_id INT NOT NULL,
    volume_id INT DEFAULT NULL,
    chapter_no INT NOT NULL,
    title VARCHAR(200) DEFAULT '',
    content LONGTEXT,
    word_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
    INDEX idx_chapters_work (work_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 版本快照表
CREATE TABLE work_versions (
    version_id INT AUTO_INCREMENT PRIMARY KEY,
    work_id INT NOT NULL,
    content_json LONGTEXT NOT NULL,
    word_count INT DEFAULT 0,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
    INDEX idx_versions_work (work_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 评论表
CREATE TABLE comments (
    comment_id INT AUTO_INCREMENT PRIMARY KEY,
    work_id INT NOT NULL,
    user_id INT NOT NULL,
    parent_id INT DEFAULT NULL,
    content TEXT NOT NULL,
    is_pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES comments(comment_id) ON DELETE CASCADE,
    INDEX idx_comments_work (work_id),
    INDEX idx_comments_work_time (work_id, created_at),
    INDEX idx_comments_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. 作品点赞表
CREATE TABLE work_likes (
    like_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    work_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
    UNIQUE KEY uk_work_like (user_id, work_id),
    INDEX idx_work_likes_work (work_id),
    INDEX idx_work_likes_time (work_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6b. 评论点赞表
CREATE TABLE comment_likes (
    like_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    comment_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (comment_id) REFERENCES comments(comment_id) ON DELETE CASCADE,
    UNIQUE KEY uk_comment_like (user_id, comment_id),
    INDEX idx_comment_likes_comment (comment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. 收藏表
CREATE TABLE favorites (
    favorite_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    work_id INT NOT NULL,
    folder_name VARCHAR(100) DEFAULT '默认收藏夹',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
    UNIQUE KEY uk_favorite (user_id, work_id),
    INDEX idx_favorites_user (user_id),
    INDEX idx_favorites_work_time (work_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. 关注表
CREATE TABLE follows (
    follow_id INT AUTO_INCREMENT PRIMARY KEY,
    follower_id INT NOT NULL,
    following_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (follower_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (following_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uk_follow (follower_id, following_id),
    INDEX idx_follows_follower (follower_id),
    INDEX idx_follows_following (following_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. 挑战赛表
CREATE TABLE challenges (
    challenge_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    cover_image VARCHAR(500) DEFAULT '',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('upcoming', 'active', 'ended') DEFAULT 'upcoming',
    min_words INT DEFAULT 0,
    participant_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. 挑战参与表
CREATE TABLE challenge_participants (
    participant_id INT AUTO_INCREMENT PRIMARY KEY,
    challenge_id INT NOT NULL,
    user_id INT NOT NULL,
    progress INT DEFAULT 0,
    checkin_days INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (challenge_id) REFERENCES challenges(challenge_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uk_participant (challenge_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. 挑战打卡表
CREATE TABLE challenge_checkins (
    checkin_id INT AUTO_INCREMENT PRIMARY KEY,
    participant_id INT NOT NULL,
    checkin_date DATE NOT NULL,
    word_count INT DEFAULT 0,
    note VARCHAR(500) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (participant_id) REFERENCES challenge_participants(participant_id) ON DELETE CASCADE,
    UNIQUE KEY uk_checkin (participant_id, checkin_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. 写作记录表
CREATE TABLE writing_sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    work_id INT DEFAULT NULL,
    word_count INT DEFAULT 0,
    duration INT DEFAULT 0,
    session_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE SET NULL,
    INDEX idx_sessions_user_date (user_id, session_date),
    INDEX idx_sessions_covering (user_id, session_date, word_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. AI对话记录表
CREATE TABLE ai_conversations (
    conv_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_key VARCHAR(100) NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_conv_session (user_id, session_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 14. 通知表
CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    related_id INT DEFAULT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_notif_user (user_id, is_read, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 15. 成就定义表
CREATE TABLE achievements (
    achievement_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500) DEFAULT '',
    icon VARCHAR(50) DEFAULT '',
    condition_type VARCHAR(50) NOT NULL,
    condition_value INT NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 16. 用户成就表
CREATE TABLE user_achievements (
    ua_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    achievement_id INT NOT NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_achievement (user_id, achievement_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 17. 接龙段落表
CREATE TABLE relay_segments (
    segment_id INT AUTO_INCREMENT PRIMARY KEY,
    challenge_id INT NOT NULL,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    segment_order INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (challenge_id) REFERENCES challenges(challenge_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_relay_challenge (challenge_id, segment_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 18. 诗词素材表
CREATE TABLE poems (
    poem_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(100) NOT NULL,
    dynasty VARCHAR(50) DEFAULT '',
    content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    source VARCHAR(100) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_poem_category (category),
    INDEX idx_poem_author (author)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 19. 写作素材表
CREATE TABLE materials (
    material_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    tags VARCHAR(500) DEFAULT '',
    source VARCHAR(100) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_mat_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 20. 每日练习题目表
CREATE TABLE daily_prompts (
    prompt_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    type ENUM('micro_fiction', 'poetry', 'dialogue', 'description', 'continuation') NOT NULL,
    word_min INT DEFAULT 50,
    word_max INT DEFAULT 300,
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    tags VARCHAR(500) DEFAULT '',
    active_date DATE DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_prompt_date (active_date),
    INDEX idx_prompt_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 21. 每日练习提交表
CREATE TABLE daily_submissions (
    submission_id INT AUTO_INCREMENT PRIMARY KEY,
    prompt_id INT NOT NULL,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    word_count INT DEFAULT 0,
    likes_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prompt_id) REFERENCES daily_prompts(prompt_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uk_submission (prompt_id, user_id),
    INDEX idx_sub_prompt (prompt_id),
    INDEX idx_sub_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 22. 练习点赞表
CREATE TABLE submission_likes (
    like_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    submission_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (submission_id) REFERENCES daily_submissions(submission_id) ON DELETE CASCADE,
    UNIQUE KEY uk_sub_like (user_id, submission_id),
    INDEX idx_sub_likes (submission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 23. 卷表（出版连载）
CREATE TABLE volumes (
    volume_id INT AUTO_INCREMENT PRIMARY KEY,
    work_id INT NOT NULL,
    volume_no INT NOT NULL,
    title VARCHAR(200) DEFAULT '',
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
    INDEX idx_volumes_work (work_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 24. 角色扮演角色表
CREATE TABLE rp_characters (
    char_id INT AUTO_INCREMENT PRIMARY KEY,
    work_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    personality TEXT,
    background TEXT,
    speaking_style TEXT,
    avatar VARCHAR(500) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
    INDEX idx_rp_chars_work (work_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 25. 书库书籍表（外部导入书籍，区别于用户创作的 works 表）
CREATE TABLE library_books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(100) NOT NULL,
    summary TEXT,
    cover_image VARCHAR(500) DEFAULT '',
    type ENUM('novel', 'essay', 'poetry', 'webfiction') DEFAULT 'novel',
    tags VARCHAR(500) DEFAULT '',
    word_count INT DEFAULT 0,
    chapter_count INT DEFAULT 0,
    serialization_status ENUM('serializing', 'completed', 'paused') DEFAULT 'completed',
    source VARCHAR(100) DEFAULT '',
    uploader_id INT DEFAULT NULL,
    views INT DEFAULT 0,
    favorites_count INT DEFAULT 0,
    rating_avg DECIMAL(3,2) DEFAULT 0,
    rating_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (uploader_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_book_type (type),
    INDEX idx_book_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 26. 书库卷表（先于章节表创建，供章节表外键引用）
CREATE TABLE library_volumes (
    volume_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    volume_no INT NOT NULL,
    title VARCHAR(200) DEFAULT '',
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES library_books(book_id) ON DELETE CASCADE,
    INDEX idx_lvol_book (book_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 27. 书库章节表
CREATE TABLE library_chapters (
    chapter_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    volume_id INT DEFAULT NULL,
    chapter_no INT NOT NULL,
    title VARCHAR(200) DEFAULT '',
    content LONGTEXT,
    word_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES library_books(book_id) ON DELETE CASCADE,
    FOREIGN KEY (volume_id) REFERENCES library_volumes(volume_id) ON DELETE SET NULL,
    INDEX idx_lch_book (book_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 28. 个人书架表
CREATE TABLE reading_bookshelf (
    shelf_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_type ENUM('work', 'library') NOT NULL,
    book_id INT NOT NULL,
    shelf_group ENUM('reading', 'completed', 'want_read') DEFAULT 'want_read',
    folder_name VARCHAR(100) DEFAULT '',
    rating TINYINT DEFAULT 0,
    last_read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uk_shelf_book (user_id, book_type, book_id),
    INDEX idx_shelf_user (user_id, shelf_group)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 29. 阅读进度表
CREATE TABLE reading_progress (
    progress_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_type ENUM('work', 'library') NOT NULL,
    book_id INT NOT NULL,
    chapter_id INT DEFAULT NULL,
    chapter_no INT DEFAULT 0,
    scroll_percent DECIMAL(5,2) DEFAULT 0,
    total_percent DECIMAL(5,2) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uk_progress_book (user_id, book_type, book_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 30. 书签表
CREATE TABLE reading_bookmarks (
    bookmark_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_type ENUM('work', 'library') NOT NULL,
    book_id INT NOT NULL,
    chapter_id INT DEFAULT NULL,
    chapter_no INT DEFAULT 0,
    paragraph_index INT DEFAULT 0,
    selected_text VARCHAR(500) DEFAULT '',
    note VARCHAR(500) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_bm_user_book (user_id, book_type, book_id),
    INDEX idx_bm_chapter (user_id, book_type, book_id, chapter_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 31. 批注表
CREATE TABLE reading_annotations (
    annotation_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_type ENUM('work', 'library') NOT NULL,
    book_id INT NOT NULL,
    chapter_id INT DEFAULT NULL,
    chapter_no INT DEFAULT 0,
    paragraph_index INT DEFAULT 0,
    selected_text VARCHAR(1000) DEFAULT '',
    content TEXT NOT NULL,
    is_public TINYINT(1) DEFAULT 1,
    parent_id INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES reading_annotations(annotation_id) ON DELETE CASCADE,
    INDEX idx_ann_user_book (user_id, book_type, book_id),
    INDEX idx_ann_chapter (book_type, book_id, chapter_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 32. 阅读打卡表
CREATE TABLE reading_checkins (
    checkin_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    checkin_date DATE NOT NULL,
    read_minutes INT DEFAULT 0,
    pages_read INT DEFAULT 0,
    books_read INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uk_checkin_date (user_id, checkin_date),
    INDEX idx_checkin_user (user_id, checkin_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 33. 好句标记表
CREATE TABLE reading_highlights (
    highlight_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_type ENUM('work', 'library') NOT NULL,
    book_id INT NOT NULL,
    chapter_id INT DEFAULT NULL,
    chapter_no INT DEFAULT 0,
    selected_text VARCHAR(1000) NOT NULL,
    synced_to_material TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_hl_user_book (user_id, book_type, book_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 34. 阅读目标表
CREATE TABLE reading_goals (
    goal_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    month VARCHAR(7) NOT NULL COMMENT '格式: 2026-06',
    target_minutes INT DEFAULT 0,
    target_books INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uk_goal_month (user_id, month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 35. 书评评分表
CREATE TABLE library_reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    user_id INT NOT NULL,
    rating TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    content TEXT,
    likes_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES library_books(book_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uk_review_book_user (book_id, user_id),
    INDEX idx_review_book (book_id),
    INDEX idx_review_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 36. 阅读时长详情表（按书籍记录）
CREATE TABLE reading_time_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_type ENUM('work', 'library') NOT NULL,
    book_id INT NOT NULL,
    read_minutes INT DEFAULT 0,
    session_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_time_user_date (user_id, session_date),
    INDEX idx_time_book (book_type, book_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
