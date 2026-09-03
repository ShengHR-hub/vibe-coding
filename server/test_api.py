"""Comprehensive API test for Task 13."""
import requests
import sys

BASE = "http://localhost:5000"
s = requests.Session()
pass_count = 0
fail_count = 0
skip_count = 0


def check(label, resp, expected_code=0):
    global pass_count, fail_count
    try:
        data = resp.json()
        code = data.get("code", "?")
    except Exception:
        code = "PARSE_ERROR"
    if code == expected_code:
        print(f"  [PASS] {label} (code={code})")
        pass_count += 1
        return data
    else:
        print(f"  [FAIL] {label} (expected {expected_code}, got {code})")
        if code == "PARSE_ERROR":
            print(f"         body: {resp.text[:200]}")
        fail_count += 1
        return None


def check_ai(label, resp):
    """AI endpoints: accept code=0 or code=1 (AI unavailable is OK, crash is not)."""
    global pass_count, fail_count
    try:
        data = resp.json()
        code = data.get("code", "?")
    except Exception:
        code = "PARSE_ERROR"
    if code in (0, 1):
        print(f"  [PASS] {label} (code={code})")
        pass_count += 1
        return data
    else:
        print(f"  [FAIL] {label} (got code={code}, expected 0 or 1)")
        fail_count += 1
        return None


def check_any(label, resp, ok_codes):
    """Accept any of the given codes."""
    global pass_count, fail_count
    try:
        data = resp.json()
        code = data.get("code", "?")
    except Exception:
        code = "PARSE_ERROR"
    if code in ok_codes:
        print(f"  [PASS] {label} (code={code})")
        pass_count += 1
        return data
    else:
        print(f"  [FAIL] {label} (expected one of {ok_codes}, got {code})")
        fail_count += 1
        return None


print("=" * 50)
print("  Inkstone API Test Suite (Task 13)")
print("=" * 50)

# --- Login ---
print("\n--- Auth: Login ---")
resp = s.post(f"{BASE}/api/auth/login", json={"username": "李白", "password": "123456"})
check("Login as 李白 (valid credentials)", resp)

resp = s.get(f"{BASE}/api/auth/me")
check("GET /auth/me (authenticated)", resp)

resp = s.post(f"{BASE}/api/auth/login", json={"username": "nobody", "password": "wrong"})
check("Login wrong password", resp, expected_code=1)

resp = s.post(f"{BASE}/api/auth/login", json={"username": "", "password": ""})
check("Login empty fields", resp, expected_code=1)

# ====== STATS ======
print("\n--- Stats (Task 7) ---")

resp = s.get(f"{BASE}/api/stats/overview")
check("GET /stats/overview", resp)

resp = s.get(f"{BASE}/api/stats/overview/bar")
check("GET /stats/overview/bar", resp)

resp = s.get(f"{BASE}/api/stats/heatmap")
check("GET /stats/heatmap", resp)

resp = s.get(f"{BASE}/api/stats/style")
check_ai("GET /stats/style", resp)

resp = s.get(f"{BASE}/api/stats/report")
check_ai("GET /stats/report", resp)

resp = s.get(f"{BASE}/api/stats/sessions")
check("GET /stats/sessions", resp)

resp = s.post(f"{BASE}/api/stats/session", json={"word_count": 100, "duration": 30})
check("POST /stats/session", resp)

# Auth check
s2 = requests.Session()
resp = s2.get(f"{BASE}/api/stats/overview")
check("GET /stats/overview (no auth)", resp, expected_code=401)

# ====== GRAPH ======
print("\n--- Graph (Task 8) ---")

resp = s.get(f"{BASE}/api/community/feed")
feed_data = resp.json()
items = feed_data.get("data", {}).get("items", [])
work_id = items[0]["work_id"] if items else 1
print(f"  Using work_id={work_id}")

resp = s.get(f"{BASE}/api/graph/{work_id}/characters")
check_ai(f"GET /graph/{work_id}/characters", resp)

resp = s.get(f"{BASE}/api/graph/{work_id}/timeline")
check_ai(f"GET /graph/{work_id}/timeline", resp)

resp = s2.get(f"{BASE}/api/graph/{work_id}/characters")
check(f"GET /graph/{work_id}/characters (no auth)", resp, expected_code=401)

# ====== CHALLENGES ======
print("\n--- Challenges (Task 9) ---")

resp = s2.get(f"{BASE}/api/challenges")
check("GET /challenges (public)", resp)

resp = s2.get(f"{BASE}/api/challenges?status=active")
check("GET /challenges?status=active", resp)

resp = s.get(f"{BASE}/api/challenges?status=active")
cdata = resp.json()
citems = cdata.get("data", {}).get("items", [])
cid = citems[0]["challenge_id"] if citems else 1
print(f"  Using challenge_id={cid}")

# join — may already be joined (code=1)
resp = s.post(f"{BASE}/api/challenges/{cid}/join")
check_any(f"POST /challenges/{cid}/join", resp, ok_codes={0, 1})

resp = s.post(f"{BASE}/api/challenges/{cid}/checkin", json={"word_count": 500})
check(f"POST /challenges/{cid}/checkin", resp)

resp = s.get(f"{BASE}/api/challenges/{cid}/relay")
check(f"GET /challenges/{cid}/relay", resp)

resp = s.post(f"{BASE}/api/challenges/{cid}/relay", json={"content": "测试接力段落内容"})
check(f"POST /challenges/{cid}/relay", resp)

resp = s.get(f"{BASE}/api/challenges/{cid}/checkins")
check(f"GET /challenges/{cid}/checkins", resp)

# Edge: join non-existent challenge
resp = s.post(f"{BASE}/api/challenges/99999/join")
check("POST /challenges/99999/join (bad id)", resp, expected_code=404)

# Edge: checkin with bad data (word_count defaults to 0, still valid)
resp = s.post(f"{BASE}/api/challenges/{cid}/checkin", json={})
check(f"POST /challenges/{cid}/checkin (no word_count)", resp)

# ====== NOTIFICATIONS ======
print("\n--- Notifications (Task 10) ---")

resp = s.get(f"{BASE}/api/notifications")
check("GET /notifications", resp)

resp = s.get(f"{BASE}/api/notifications?page=1&page_size=3")
check("GET /notifications?page=1&page_size=3", resp)

resp = s.post(f"{BASE}/api/notifications/mark-read", json={"mark_all": True})
check("POST /notifications/mark-read (all)", resp)

resp = s.get(f"{BASE}/api/notifications")
ndata = resp.json()
nitems = ndata.get("data", {}).get("items", [])
if nitems:
    nid = nitems[0]["notification_id"]
    resp = s.post(f"{BASE}/api/notifications/mark-read", json={"notification_id": nid})
    check(f"POST /notifications/mark-read (single id={nid})", resp)
else:
    print("  [SKIP] No notifications for single mark-read")

resp = s2.get(f"{BASE}/api/notifications")
check("GET /notifications (no auth)", resp, expected_code=401)

# ====== REVIEW ======
print("\n--- Review (Task 11) ---")

resp = s.post(f"{BASE}/api/review/generate", json={"work_id": work_id})
check_ai(f"POST /review/generate (work_id={work_id})", resp)

resp = s.get(f"{BASE}/api/review/recommend")
check_ai("GET /review/recommend", resp)

resp = s2.get(f"{BASE}/api/review/similar/{work_id}")
check(f"GET /review/similar/{work_id} (public)", resp)

# Edge cases
resp = s.post(f"{BASE}/api/review/generate", json={})
check("POST /review/generate (no work_id)", resp, expected_code=400)

resp = s.post(f"{BASE}/api/review/generate", json={"work_id": 99999})
check("POST /review/generate (bad id)", resp, expected_code=404)

# ====== Interactions (notification hooks) ======
print("\n--- Interactions (Task 10 hooks) ---")

resp = s.post(f"{BASE}/api/interactions/like", json={"work_id": work_id})
check("POST /interactions/like", resp)

resp = s.post(f"{BASE}/api/interactions/favorite", json={"work_id": work_id})
check("POST /interactions/favorite", resp)

resp = s.post(f"{BASE}/api/interactions/comments", json={"work_id": work_id, "content": "写得真好！"})
check("POST /interactions/comments", resp)

# Verify notification was created for the comment
resp = s.get(f"{BASE}/api/notifications")
ndata = resp.json()
nitems = ndata.get("data", {}).get("items", [])
if nitems:
    print(f"  [INFO] Latest notification: {nitems[0].get('content', '')} (type={nitems[0].get('type', '')})")

# ====== Users ======
print("\n--- Users (Task 10 hooks) ---")

# follow — may already follow (code=1)
resp = s.post(f"{BASE}/api/users/follow", json={"following_id": 2})
check_any("POST /users/follow", resp, ok_codes={0, 1})

# ====== Works (public + CRUD) ======
print("\n--- Works ---")

resp = s2.get(f"{BASE}/api/works/public/{work_id}")
check(f"GET /works/public/{work_id} (public)", resp)

resp = s2.get(f"{BASE}/api/works/public/99999")
check("GET /works/public/99999 (bad id)", resp, expected_code=404)

resp = s.get(f"{BASE}/api/works")
check("GET /works (my works)", resp)

resp = s.get(f"{BASE}/api/community/feed")
check("GET /community/feed", resp)

resp = s2.get(f"{BASE}/api/community/search?q=诗")
check("GET /community/search?q=诗", resp)

# ====== SUMMARY ======
print("\n" + "=" * 50)
total = pass_count + fail_count
print(f"  Results: {pass_count}/{total} passed, {fail_count} failed")
print("=" * 50)

sys.exit(0 if fail_count == 0 else 1)
