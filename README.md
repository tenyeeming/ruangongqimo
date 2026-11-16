# 投稿審查系統

軟體工程期中個人專題。用 FastAPI 實作的簡單投稿審查網站，有作者和編輯兩種角色。

## 功能

**作者**
- 查看自己的投稿清單（類別、標題、審查狀態）
- 新增 / 編輯投稿（類別、標題、文章內容），新增的稿件狀態為「編輯中」
- 刪除編輯中的稿件
- 送出投稿：編輯中 → 審查中

**編輯**
- 查看待審查清單（作者、類別、標題）
- 查看稿件內容
- 通過：審查中 → 已通過
- 退回：審查中 → 編輯中

稿件狀態：編輯中、審查中、已通過

```
編輯中 --送出--> 審查中 --通過--> 已通過
  ^                |
  +------退回------+
```

## 執行方式

需要 Python 3.10 以上。

```bash
python -m venv .venv
.venv\Scripts\activate        # macOS / Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

打開 http://127.0.0.1:8000 就可以使用，API 文件在 http://127.0.0.1:8000/docs 。

第一次啟動會自動建立 `data.db` 和測試帳號（密碼都是 `123456`）：

| 帳號 | 名稱 | 角色 |
|------|------|------|
| author1 | 王小明 | 作者 |
| author2 | 李小華 | 作者 |
| editor1 | 陳編輯 | 編輯 |

同時會放入兩篇範例稿件：王小明的一篇「審查中」、李小華的一篇「編輯中」。

想重置資料的話把 `data.db` 刪掉再重新啟動即可。

## 測試

```bash
python -m pytest
```

## 使用技術

- FastAPI
- SQLModel + SQLite
- Jinja2（網頁畫面）
- Session cookie 登入，密碼用 PBKDF2 雜湊
- pytest

## 專案結構

```
app/
  main.py          程式進入點、錯誤處理
  database.py      資料庫連線、建立預設帳號
  models.py        資料表（User、Manuscript）與狀態定義
  auth.py          登入、密碼雜湊、角色檢查
  services.py      稿件操作與狀態轉換規則
  schemas.py       API 的輸入輸出格式
  routers/
    account.py     /api/login、/api/logout、/api/me
    author.py      作者 API（/api/manuscripts）
    editor.py      編輯 API（/api/reviews）
    pages.py       網頁畫面
  templates/       HTML 樣板
  static/          CSS
tests/             API 與頁面測試
```

## API

| 方法 | 路徑 | 角色 | 說明 |
|------|------|------|------|
| POST | /api/login | - | 登入 |
| POST | /api/logout | - | 登出 |
| GET | /api/me | 已登入 | 目前使用者 |
| GET | /api/manuscripts | 作者 | 我的稿件清單 |
| POST | /api/manuscripts | 作者 | 新增稿件 |
| GET | /api/manuscripts/{id} | 作者 | 稿件內容 |
| PUT | /api/manuscripts/{id} | 作者 | 修改稿件（限編輯中） |
| DELETE | /api/manuscripts/{id} | 作者 | 刪除稿件（限編輯中） |
| POST | /api/manuscripts/{id}/submit | 作者 | 送出投稿 |
| GET | /api/reviews | 編輯 | 待審查清單 |
| GET | /api/reviews/{id} | 編輯 | 稿件內容 |
| POST | /api/reviews/{id}/approve | 編輯 | 通過 |
| POST | /api/reviews/{id}/reject | 編輯 | 退回 |

錯誤代碼：401 未登入、403 角色不符或不是自己的稿件、404 找不到、409 稿件狀態不允許這個操作、400 欄位錯誤。

## 規則補充

- 作者只能看到、修改自己的稿件
- 只有「編輯中」的稿件可以修改或刪除，送出後就不能再改，除非被編輯退回
- 內容空白的稿件不能送出
- 編輯只看得到「審查中」的稿件
