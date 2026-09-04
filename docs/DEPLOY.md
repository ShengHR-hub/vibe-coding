# 墨池 Inkstone · 生产部署手册（DEPLOY）

适用版本：v2026.09.04（成书工作流版）。目标环境：Linux（Ubuntu 22.04）单机部署：
**Nginx(443) → Gunicorn(Flask) → MySQL**，含 HTTPS 与腾讯云域名接入。

---

## 1. 架构总览

```
用户浏览器
   │ https://你的域名
   ▼
Nginx 443（静态 client/dist + /api、/uploads 反向代理）
   │ 反向代理
   ▼
Gunicorn（Unix socket, 2-4 worker）→ Flask app.py::create_app()
   │
   ▼
MySQL 8（inkstone 库）
MiMo API（由后端出网调用，无需额外部署）
```

## 2. 服务器与系统准备

- 建议规格：2 vCPU / 2-4GB 内存 / 40-60GB SSD（MySQL + 代码 + 日志足够；并发不高 2G 可用，建议开 1GB swap）。
- 系统：Ubuntu 22.04 LTS。放行安全组端口：80、443、（可选 22 限定来源）。
- 中文/编码：确保 MySQL 使用 utf8mb4（schema 已内置）。

## 3. 一键脚本（复制到服务器 Bash 执行，分步）

```bash
# 3.1 基础软件
sudo apt update && sudo apt install -y python3-venv python3-pip nginx mysql-server git
sudo mysql_secure_installation            # 设置 root 密码并加固

# 3.2 应用目录与代码
sudo mkdir -p /srv/inkstone
sudo chown $USER /srv/inkstone
git clone <你的GitHub存档地址> /srv/inkstone
cd /srv/inkstone

# 3.3 后端依赖 + 环境变量
cd server
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt gunicorn   # 生产额外安装 gunicorn
cp .env.example .env                        # 填入 SECRET_KEY / MySQL 密码 / MIMO_API_KEY
# 修改 .env：MYSQL_HOST=127.0.0.1 MYSQL_USER=inkstone MYSQL_PASSWORD=*** MYSQL_DB=inkstone

# 3.4 数据库初始化（建用户与库）
mysql -u root -p <<'SQL'
CREATE DATABASE inkstone CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'inkstone'@'localhost' IDENTIFIED BY '强密码';
GRANT ALL ON inkstone.* TO 'inkstone'@'localhost';
FLUSH PRIVILEGES;
SQL
mysql -u inkstone -p inkstone < server/database/schema.sql
cd server && .venv/bin/python -m database.seed

# 3.5 前端构建（Flask 静态托管 client/dist）
cd client && npm ci && npm run build
```

## 4. Gunicorn 服务（systemd）

`sudo nano /etc/systemd/system/inkstone.service`：

```ini
[Unit]
Description=Inkstone Flask (Gunicorn)
After=network.target mysql.service

[Service]
WorkingDirectory=/srv/inkstone/server
EnvironmentFile=/srv/inkstone/server/.env
ExecStart=/srv/inkstone/server/.venv/bin/gunicorn -w 3 -b 127.0.0.1:8000 \
  --timeout 180 'app:create_app()'
Restart=always
User=www-data
Group=www-data
# 允许 Flask 写 uploads：先 chown -R www-data /srv/inkstone/server/uploads

[Install]
WantedBy=multi-user.target
```

```bash
sudo mkdir -p /srv/inkstone/server/uploads && sudo chown -R www-data /srv/inkstone/server
sudo systemctl daemon-reload && sudo systemctl enable --now inkstone
# 自检：curl http://127.0.0.1:8000/api/health
```

> SSE（续写/对话流式）经 Gunicorn + Nginx 可用；Nginx 需关闭缓冲以逐字转发（见下）。

## 5. Nginx 站点

`sudo nano /etc/nginx/sites-available/inkstone`：

```nginx
server {
    listen 80;
    server_name 你的域名.com;

    client_max_body_size 60m;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;              # SSE：关缓冲逐字下发
        proxy_read_timeout 300s;
    }
    location /uploads/ { proxy_pass http://127.0.0.1:8000; }

    location / {
        proxy_pass http://127.0.0.1:8000;  # 生产直接由 Flask 托管 dist
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/inkstone /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

> 也可用本仓库分支方案：Nginx 直接 serve `/srv/inkstone/client/dist` 静态 + 反代 `/api`，
> 两种皆可；Flask 内置托管已可用则上面配置最简。

## 6. HTTPS（Let's Encrypt）与腾讯云域名

1. **腾讯云域名解析**：DNSPod 控制台 → 该域名 → 添加记录 `A 类型 @ / www → 服务器公网 IP`。
   - ⚠️ 若服务器为中国大陆地域，域名需完成 **ICP 备案**（阿里云备案入口）才能被访问；未备案请选**香港/新加坡等免备案地域**。
2. **签发证书**：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d 你的域名.com -d www.你的域名.com
```

3. 浏览器访问 `https://你的域名.com` 验证。

## 7. Session 安全（上线必改）

- `server/.env`：`SECRET_KEY` 用长随机串；`AI_RATE_PER_MIN / AI_DAILY_LIMIT` 按预算调小。
- Flask 默认 session cookie：生产建议在 `config.py` 按需开启
  `SESSION_COOKIE_SECURE=True`（仅 HTTPS 下访问）——本版未强制，HTTPS 就绪后开启。

## 8. 备份与升级

```bash
# 每日备份（crontab -e）：库 + 上传目录 + .env
mysqldump -uinkstone -p'***' inkstone | gzip > /srv/backup/inkstone-$(date +%F).sql.gz
rsync -a /srv/inkstone/server/uploads /srv/backup/uploads/
```

升级流程：`git pull` → 若有新表执行幂等 ALTER/建表 → `cd client && npm run build`
→ `sudo systemctl restart inkstone`。

## 9. 上线自检清单

- [ ] `/api/health` 返回 ok；`/` 返回前端
- [ ] 注册/登录 → 建书 → 保存 → `/write?work=ID` 打开
- [ ] 灵感馆 /inspire 浏览/收藏/收录
- [ ] AI 续写流式逐字出现（配额按 .env）
- [ ] 广场点击作品 → 公开详情页；评论/点赞/收藏正常
- [ ] HTTPS 生效、无混合内容警告
- [ ] 服务器磁盘/内存/日志（journalctl -u inkstone）无异常
