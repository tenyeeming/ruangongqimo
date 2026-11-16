def new_draft(client, title="測試稿件", content="內容"):
    r = client.post("/api/manuscripts", json={"category": "論文", "title": title, "content": content})
    assert r.status_code == 201
    return r.json()


def submitted(client, **kw):
    m = new_draft(client, **kw)
    r = client.post(f"/api/manuscripts/{m['id']}/submit")
    assert r.status_code == 200
    return r.json()


# ---------- 登入與權限 ----------

def test_login_wrong_password(make_client):
    client = make_client()
    r = client.post("/api/login", json={"username": "author1", "password": "wrong"})
    assert r.status_code == 401


def test_not_logged_in(make_client):
    client = make_client()
    assert client.get("/api/manuscripts").status_code == 401
    assert client.get("/api/reviews").status_code == 401


def test_me(author):
    r = author.get("/api/me")
    assert r.json()["username"] == "author1"
    assert r.json()["role"] == "author"


def test_role_check(author, editor):
    assert author.get("/api/reviews").status_code == 403
    assert editor.get("/api/manuscripts").status_code == 403


def test_logout(author):
    author.post("/api/logout")
    assert author.get("/api/manuscripts").status_code == 401


# ---------- 作者 ----------

def test_create_is_draft(author):
    m = new_draft(author)
    assert m["status"] == "編輯中"
    r = author.get("/api/manuscripts")
    assert [x["title"] for x in r.json()] == ["測試稿件"]


def test_create_validation(author):
    r = author.post("/api/manuscripts", json={"category": "論文", "title": "   ", "content": ""})
    assert r.status_code == 400
    r = author.post("/api/manuscripts", json={"category": "不存在", "title": "a", "content": ""})
    assert r.status_code == 400


def test_update_draft(author):
    m = new_draft(author)
    r = author.put(f"/api/manuscripts/{m['id']}",
                   json={"category": "心得", "title": "改過的標題", "content": "新內容"})
    assert r.status_code == 200
    assert r.json()["title"] == "改過的標題"
    assert r.json()["category"] == "心得"


def test_delete_draft(author):
    m = new_draft(author)
    assert author.delete(f"/api/manuscripts/{m['id']}").status_code == 204
    assert author.get(f"/api/manuscripts/{m['id']}").status_code == 404


def test_submit(author):
    m = submitted(author)
    assert m["status"] == "審查中"


def test_submit_empty_content(author):
    m = new_draft(author, content="  ")
    assert author.post(f"/api/manuscripts/{m['id']}/submit").status_code == 400


def test_cannot_change_after_submit(author):
    m = submitted(author)
    mid = m["id"]
    body = {"category": "論文", "title": "x", "content": "y"}
    assert author.put(f"/api/manuscripts/{mid}", json=body).status_code == 409
    assert author.delete(f"/api/manuscripts/{mid}").status_code == 409
    assert author.post(f"/api/manuscripts/{mid}/submit").status_code == 409


def test_other_author_cannot_touch(author, make_client):
    m = new_draft(author)
    other = make_client("author2")
    assert other.get(f"/api/manuscripts/{m['id']}").status_code == 403
    assert other.delete(f"/api/manuscripts/{m['id']}").status_code == 403
    assert other.get("/api/manuscripts").json() == []


# ---------- 編輯 ----------

def test_review_list_only_reviewing(author, editor):
    new_draft(author, title="草稿")
    submitted(author, title="送審的")
    rows = editor.get("/api/reviews").json()
    assert [r["title"] for r in rows] == ["送審的"]
    assert rows[0]["author"] == "王小明"


def test_editor_cannot_see_draft(author, editor):
    m = new_draft(author)
    assert editor.get(f"/api/reviews/{m['id']}").status_code == 404


def test_review_detail(author, editor):
    m = submitted(author, content="正文")
    r = editor.get(f"/api/reviews/{m['id']}")
    assert r.status_code == 200
    assert r.json()["content"] == "正文"


def test_approve(author, editor):
    m = submitted(author)
    r = editor.post(f"/api/reviews/{m['id']}/approve")
    assert r.json()["status"] == "已通過"
    assert editor.get("/api/reviews").json() == []
    assert author.get(f"/api/manuscripts/{m['id']}").json()["status"] == "已通過"


def test_reject_then_edit_again(author, editor):
    m = submitted(author)
    r = editor.post(f"/api/reviews/{m['id']}/reject")
    assert r.json()["status"] == "編輯中"
    # 退回後作者可以再修改、再送出
    body = {"category": "論文", "title": "修改後", "content": "補充內容"}
    assert author.put(f"/api/manuscripts/{m['id']}", json=body).status_code == 200
    assert author.post(f"/api/manuscripts/{m['id']}/submit").status_code == 200


def test_approve_wrong_status(author, editor):
    m = new_draft(author)
    assert editor.post(f"/api/reviews/{m['id']}/approve").status_code == 409
    assert editor.post(f"/api/reviews/{m['id']}/reject").status_code == 409

    m = submitted(author, title="b")
    editor.post(f"/api/reviews/{m['id']}/approve")
    assert editor.post(f"/api/reviews/{m['id']}/approve").status_code == 409
    assert editor.post(f"/api/reviews/{m['id']}/reject").status_code == 409


def test_approve_not_found(editor):
    assert editor.post("/api/reviews/999/approve").status_code == 404
