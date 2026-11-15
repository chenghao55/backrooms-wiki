# Backrooms Archive

**一個由 AI Agent 協助維護、可持續擴充的繁體中文 Backrooms 層級檔案館。**

Backrooms Archive 是以 [Backrooms Wikidot](https://backrooms-wiki.wikidot.com/) 為資料來源的靜態網站，透過結構化 JSON 資料呈現各個 Backrooms Level 的環境描述、圖片及出入口關係。

本專案的核心不只是建立 Wiki 網站，而是透過 `AGENTS.md` 與 Agent Skill，讓 AI 能遵循統一規範，持續研究、整理並新增 Level。

**網站：** [GitHub Page](https://chenghao55.github.io/backrooms-wiki/)

## 功能特色

- **繁體中文文章：** 依照 Wikidot 原始文章，保留主要章節順序與重要設定，整理成易於閱讀的繁體中文內容。
    
- **層級搜尋與瀏覽：** 依 Level 編號或名稱尋找已收錄的層級。
    
- **出入口連結：** 透過文章中的出入口資訊，在不同 Level 之間探索。
    
- **Placeholder 機制：** 尚未收錄的層級會顯示佔位頁面，未來匯入後自動升級為完整文章。
    
- **AI Agent 擴充：** 使用 Agent Skill 將新增 Level 的工作標準化。
    
- **自動資料驗證：** 使用 Python 腳本檢查資料格式並產生索引。
    

## 技術架構

|技術|用途|
|---|---|
|HTML / CSS / JavaScript|靜態網站前端|
|JSON|儲存 Level 文章及層級關係|
|Python|資料驗證與索引生成|
|AGENTS.md|AI 開發規範|
|Agent Skill|自動化 Level 匯入流程|
|GitHub Pages|靜態網站部署|

網站不需要後端伺服器，也不會在使用者瀏覽時呼叫 AI API。AI 主要用於開發與資料整理階段。

## AI Agent 開發流程

本專案透過兩份文件規範 AI 的工作：

### AGENTS.md

定義專案整體開發原則，包括：

- 僅使用 Backrooms Wikidot 作為設定來源。
    
- 以繁體中文整理文章，不自行創作原文沒有的設定。
    
- 遵守統一 JSON Schema。
    
- 確認圖片來源與授權。
    
- 維持入口、出口的方向性。
    
- 修改資料後必須執行驗證。
    

### Agent Skill

`.agents/skills/add-backrooms-level/SKILL.md`

定義新增或完成 Level 的標準操作：

1. 讀取專案規範。
    
2. 取得指定 Level 的 Wikidot 原始文章。
    
3. 整理章節、圖片、入口及出口資訊。
    
4. 產生符合 Schema 的 Level JSON。
    
5. 為尚未收錄的數字出口建立 Placeholder。
    
6. 驗證資料並重新產生索引。
    

例如，開發者可以要求 AI：

> 請依照 add-backrooms-level Skill，新增 Level 0。

AI 便能依照既有規則執行資料匯入，而不需要為每個 Level 重新編寫前端頁面。

## 資料結構

每個 Level 使用獨立資料夾：

```
data/
├── index.json
└── levels/
    ├── level-0/
    │   ├── index.json
    │   └── images/
    ├── level-1/
    │   └── index.json
    └── level-37/
        ├── index.json
        └── images/
```

其中：

- `data/index.json`：自動產生的層級目錄。
    
- `level-{id}/index.json`：單一層級的完整資料或 Placeholder。
    
- `images/`：經確認來源與授權後儲存的圖片。
    

## 資料驗證

新增或修改 Level 後，依序執行：

```
python scripts/validate.py --source-only
python scripts/build_index.py
python scripts/validate.py
```

第一步檢查來源資料，第二步產生索引，第三步確認索引與來源資料一致。

若來源資料存在驗證錯誤，索引產生程序會拒絕更新。

## 本機執行

本專案使用靜態網站架構，可透過 Python 啟動本機 HTTP 伺服器：

```
python -m http.server 8000
```
(專案資料夾)

接著在瀏覽器開啟：

`http://localhost:8000`

請從專案根目錄啟動伺服器，避免 JSON 資料路徑錯誤。

## 未來規劃

- 持續收錄更多 Backrooms Level。
    
- 擴充層級之間的連結與探索功能。
    
- 建立互動式層級關係圖。
    
- 改善搜尋與文章閱讀體驗。
    

## 資料來源與授權

Backrooms 文章內容取自 [Backrooms Wikidot](https://backrooms-wiki.wikidot.com/)，並經過繁體中文整理與重新編排。

原始文章、圖片與其他素材的著作權及授權條件以各自來源標示為準。本專案會盡可能保留來源、作者及授權資訊。

本專案為課程學習與非官方整理作品，並非 Backrooms Wikidot 官方網站。
