"""Comprehensive full-system test — all 45 endpoints + frontend routes."""
import requests
import urllib3
import json
import sys

urllib3.disable_warnings()
BASE = "http://localhost:5000"
FE = "http://localhost:5173"
s = requests.Session()
total = 0
passed = 0

def check(label, ok, detail=""):
    global total, passed
    total += 1
    if ok:
        passed += 1
        print(f"  [OK] {label}{' — ' + detail if detail else ''}")
    else:
        print(f"  [FAIL] {label}{' — ' + detail if detail else ''}")
    return ok

def test_api(method, path, expected_code=0, body=None, auth=True, ok_codes=None):
    try:
        sess = s if auth else requests.Session()
        if method == "GET":
            resp = sess.get(f"{BASE}{path}", timeout=120)
        elif method == "DELETE":
            resp = sess.delete(f"{BASE}{path}", timeout=30)
        elif method == "PUT":
            resp = sess.put(f"{BASE}{path}", json=body, timeout=30)
        else:
            resp = sess.post(f"{BASE}{path}", json=body, timeout=120)
        code = resp.json().get("code", "PARSE")
        expected = ok_codes if ok_codes else {expected_code}
        return check(f"{method} {path}", code in expected,
                     f"code={code}" if code not in expected else "")
    except Exception as e:
        return check(f"{method} {path}", False, f"{type(e).__name__}: {str(e)[:60]}")

def test_page(path):
    try:
        resp = requests.get(f"{FE}{path}", timeout=10)
        ok = resp.status_code == 200 and 'id="app"' in resp.text
        return check(f"PAGE {path}", ok,
                     f"status={resp.status_code}" if not ok else "")
    except Exception as e:
        return check(f"PAGE {path}", False, str(e)[:60])


print("=" * 55)
print("  Inkstone Full System Test")
print("=" * 55)

# ── Login ──
print("\n═══ 1. Auth (4) ═══")
test_api("POST", "/api/auth/login", body={"username":"李白","password":"123456"})
test_api("GET", "/api/auth/me")
test_api("POST", "/api/auth/login", 1, {"username":"x","password":"x"}, auth=False)
test_api("POST", "/api/auth/login", 1, {"username":"","password":""}, auth=False)

# ── Get dynamic IDs ──
me = s.get(f"{BASE}/api/auth/me").json()
my_id = me.get("data", {}).get("user_id")
my_works = s.get(f"{BASE}/api/works").json().get("data", {}).get("items", [])
my_work_id = my_works[0]["work_id"] if my_works else None
print(f"\n  my user_id={my_id}, first work_id={my_work_id}")

# Find a public work NOT by me
feed = requests.get(f"{BASE}/api/community/feed").json()
pub_items = feed.get("data", {}).get("items", [])
pub_work_id = None
for w in pub_items:
    if w["user_id"] != my_id:
        pub_work_id = w["work_id"]
        break
if not pub_work_id and pub_items:
    pub_work_id = pub_items[0]["work_id"]
print(f"  public work_id={pub_work_id}")

# Find active challenge
ch_list = requests.get(f"{BASE}/api/challenges?status=active").json()
ch_items = ch_list.get("data", {}).get("items", [])
cid = ch_items[0]["challenge_id"] if ch_items else None
print(f"  challenge_id={cid}")

# ── AI Writing (6) ──
print("\n═══ 2. AI Writing (6) ═══")
test_api("POST", "/api/write/inspire", body={"keywords":"江湖 剑 侠客"})
test_api("POST", "/api/write/outline", body={"theme":"末世最后一个图书馆"})
test_api("POST", "/api/write/character", body={"story_context":"赛博朋克侦探"})
test_api("POST", "/api/write/polish", body={"text":"他很生气地走出去了。","mode":"文艺"})
test_api("POST", "/api/write/prompt", body={"context":"主角在沙漠迷路了三天"})
test_api("POST", "/api/write/continue", 1, {"content":""})  # empty content returns code=1

# ── Works (8 endpoints that don't destroy data) ──
print("\n═══ 3. Works (8) ═══")
test_api("POST", "/api/works", body={"title":"API测试","type":"novel","summary":"test","tags":"test"})
test_api("GET", "/api/works")
if my_work_id:
    test_api("GET", f"/api/works/{my_work_id}")
    test_api("PUT", f"/api/works/{my_work_id}", body={"title":"已修改标题"})
    test_api("GET", f"/api/works/{my_work_id}/versions")
test_api("GET", f"/api/works/99999", 404)
if pub_work_id:
    test_api("GET", f"/api/works/public/{pub_work_id}", auth=False)
# Delete the temp work we created
my_works2 = s.get(f"{BASE}/api/works").json().get("data", {}).get("items", [])
for w in my_works2:
    if w["title"] == "API测试":
        test_api("DELETE", f"/api/works/{w['work_id']}")
        break

# ── Community (3) ──
print("\n═══ 4. Community (3) ═══")
test_api("GET", "/api/community/feed", auth=False)
test_api("GET", "/api/community/search?q=诗", auth=False)
test_api("GET", "/api/community/category/novel", auth=False)

# ── Interactions (5) ──
print("\n═══ 5. Interactions (5) ═══")
if pub_work_id:
    test_api("POST", "/api/interactions/like", body={"work_id": pub_work_id})
    test_api("POST", "/api/interactions/favorite", body={"work_id": pub_work_id})
    test_api("POST", "/api/interactions/comments", body={"work_id": pub_work_id, "content":"写得真好！"})
    test_api("GET", f"/api/interactions/comments/{pub_work_id}", auth=False)
    test_api("GET", f"/api/interactions/comments/99999", auth=False)

# ── Users (5) ──
print("\n═══ 6. Users (5) ═══")
test_api("GET", f"/api/users/{my_id}", auth=False)
test_api("GET", f"/api/users/{my_id}/followers")
test_api("GET", f"/api/users/{my_id}/following")
test_api("GET", "/api/users/achievements")
test_api("GET", "/api/users/99999", 404, auth=False)

# ── Stats (7) ──
print("\n═══ 7. Stats (7) ═══")
for name in ["overview", "overview/bar", "heatmap", "style", "report", "sessions"]:
    test_api("GET", f"/api/stats/{name}")
test_api("POST", "/api/stats/session", body={"word_count":200, "duration":60})

# ── Graph (2) ──
print("\n═══ 8. Graph (2) ═══")
target = pub_work_id or my_work_id
if target:
    test_api("GET", f"/api/graph/{target}/characters")
    test_api("GET", f"/api/graph/{target}/timeline")

# ── Challenges (6) ──
print("\n═══ 9. Challenges (6) ═══")
test_api("GET", "/api/challenges", auth=False)
if cid:
    test_api("POST", f"/api/challenges/{cid}/join", ok_codes={0, 1})
    test_api("POST", f"/api/challenges/{cid}/checkin", body={"word_count":500, "note":"打卡"})
    test_api("GET", f"/api/challenges/{cid}/relay")
    test_api("POST", f"/api/challenges/{cid}/relay", body={"content":"接力测试段落"})
    test_api("GET", f"/api/challenges/{cid}/checkins")
test_api("POST", "/api/challenges/99999/join", 404)

# ── Notifications (2) ──
print("\n═══ 10. Notifications (2) ═══")
test_api("GET", "/api/notifications")
test_api("POST", "/api/notifications/mark-read", body={"mark_all": True})

# ── Review (3) ──
print("\n═══ 11. Review (3) ═══")
if target:
    test_api("POST", "/api/review/generate", body={"work_id": target})
test_api("GET", "/api/review/recommend")
if target:
    test_api("GET", f"/api/review/similar/{target}", auth=False)

# ── Logout + Register ──
print("\n═══ 12. Auth — Logout/Register ═══")
test_api("POST", "/api/auth/logout")
import random, string
rand_user = "test_" + "".join(random.choices(string.ascii_lowercase, k=6))
test_api("POST", "/api/auth/register", body={"username": rand_user, "password": "123456"}, auth=False)

# Login back
test_api("POST", "/api/auth/login", body={"username":"李白","password":"123456"})
# Follow someone else
others = [r["user_id"] for r in requests.get(f"{BASE}/api/users/{my_id}/following").json().get("data",{}).get("items",[])]
target_uid = next((u for u in [1,2,3,4,5] if u != my_id and u not in others), None)
if target_uid:
    test_api("POST", "/api/users/follow", body={"following_id": target_uid}, ok_codes={0, 1})

# ── Frontend (14) ──
print("\n═══ 13. Frontend Pages (14) ═══")
for p in ["/", "/login", "/register", "/explore", "/challenges",
          "/write", "/works", "/stats", "/notifications",
          f"/graph/{target}", f"/review/{target}", f"/read/{target}",
          f"/profile/{my_id}", f"/works/{my_work_id}/edit"]:
    test_page(p)

# ── Summary ──
print("\n" + "=" * 55)
print(f"  Total: {passed}/{total} passed ({total-passed} failed)")
print(f"  Backend API: {passed - 14}/{total - 14}  |  Frontend: validating 14 pages")
print("=" * 55)
sys.exit(0 if passed == total else 1)
