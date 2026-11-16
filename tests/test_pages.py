def page_login(client, username):
    r = client.post("/login", data={"username": username, "password": "123456"},
                    follow_redirects=False)
    assert r.status_code == 303
    return r


def test_redirect_to_login(make_client):
    client = make_client()
    r = client.get("/author", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_login_page_wrong_password(make_client):
    client = make_client()
    r = client.post("/login", data={"username": "author1", "password": "x"})
    assert r.status_code == 400
    assert "帳號或密碼錯誤" in r.text


def test_index_redirect_by_role(make_client):
    a = make_client()
    page_login(a, "author1")
    assert a.get("/", follow_redirects=False).headers["location"] == "/author"

    e = make_client()
    page_login(e, "editor1")
    assert e.get("/", follow_redirects=False).headers["location"] == "/editor"


def test_full_flow(make_client):
    a = make_client()
    page_login(a, "author1")

    r = a.post("/author/new", data={"category": "心得", "title": "我的心得", "content": "很好"})
    assert r.status_code == 200
    assert "我的心得" in r.text
    assert "編輯中" in r.text

    mid = a.get("/api/manuscripts").json()[0]["id"]
    r = a.post(f"/author/{mid}/submit")
    assert "已送出投稿" in r.text

    e = make_client()
    page_login(e, "editor1")
    r = e.get("/editor")
    assert "我的心得" in r.text and "王小明" in r.text
    r = e.get(f"/editor/{mid}")
    assert "很好" in r.text
    r = e.post(f"/editor/{mid}/approve")
    assert "已通過" in r.text

    r = a.get("/author")
    assert "已通過" in r.text


def test_save_and_submit_button(make_client):
    a = make_client()
    page_login(a, "author1")
    r = a.post("/author/new", data={"category": "論文", "title": "t", "content": "c",
                                    "action": "submit"})
    assert "已送出投稿" in r.text
    assert a.get("/api/manuscripts").json()[0]["status"] == "審查中"


def test_form_error_keeps_input(make_client):
    a = make_client()
    page_login(a, "author1")
    r = a.post("/author/new", data={"category": "論文", "title": "", "content": "保留這段"})
    assert r.status_code == 400
    assert "標題不能空白" in r.text
    assert "保留這段" in r.text


def test_wrong_role_page(make_client):
    a = make_client()
    page_login(a, "author1")
    r = a.get("/editor")
    assert r.status_code == 403
    assert "只有編輯" in r.text
