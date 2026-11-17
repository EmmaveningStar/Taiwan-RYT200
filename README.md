# 台灣瑜珈師培地圖

台灣 RYT200 瑜珈師資培訓索引。依縣市與關鍵字查課程，並以 GitHub Issues 儲存讀者投稿。

## GitHub 初次設定

1. 建立公開 repository，建議命名為 `ryt200-taiwan`。將壓縮檔內的內容放進 repository 根目錄，包含隱藏目錄 `.github`。
2. 在 Settings → Pages → Build and deployment → Source 選 GitHub Actions。確認 Issues 已啟用，在 Issues → Labels 新增「讀者投稿」和「已核准」。
3. 要啟用自動網路探索，到 Settings → Secrets and variables → Actions 新增 repository secret `BRAVE_SEARCH_API_KEY`。
4. 在 Actions → 更新課程網站 → Run workflow 執行一次。部署成功後，到 Settings → Pages 開啟站點並確認投稿入口。
5. 功能驗收可建立一筆測試投稿，先確認網站讀者區未新增，再貼上「已核准」標籤並等候部署。確認讀者區顯示後，可移除標籤或刪除測試內容。

## 日常維護

- Actions 每天台灣時間 07:23 排程執行，實際執行時間可能延後。就算搜尋服務失敗，網站仍可用既有的正式課程。
- 工作流程附件 `course-source-review/review.json` 含既有官方頁面指紋、搜尋候選及警告。頁面指紋也可能因版面或廣告異動而改變。搜尋使用 Brave 的網頁索引，並對 Facebook、Threads 網域查詢；可發現被索引的公開頁面，覆蓋率受索引限制。Google 或 Meta API 未接入，沒有登入抓取留言。
- 檢查候選連結後，把已確認的課程加入 `site/data.json` 的 `courses`，同一學校的不同班別使用獨立 ID。更新 `checked` 為最近一次人工核對日期。學費、招生狀態、開課時間或 Yoga Alliance 資格，應以對應的主辦公告或學校資料為準。
- 投稿原始資料在 GitHub Issues，公開網站鏡像已加上「讀者投稿」與「已核准」兩個標籤的工單正文。維護者可移除「已核准」撤下內容。核准補充課程後，如需出現在課程搜尋結果，還要把核對後資料加入課程列表。

## 本機預覽

`python3 -m http.server 8000 --directory site`，開啟 http://localhost:8000。
