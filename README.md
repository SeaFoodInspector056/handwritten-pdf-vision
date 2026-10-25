# Goodnotes PDF Vision

作者：[海鮮稽查長 SeaFoodInspector](https://github.com/SeaFoodInspector056)

版本：1.1.0

給具備程式執行與圖片檢視能力的 Codex／相容 agent 使用：從 Google Drive 或本機取得 PDF，將指定頁面渲染為 PNG，實際看圖後解釋手寫筆記、公式與圖形。使用 PyMuPDF，不以 OCR 或 PDF 抽取文字取代頁面圖片。

## 安裝

將本資料夾安裝為 Codex 可探索到的 `goodnotes-pdf-vision` 技能資料夾。若使用 Codex 的 skill-installer，可提供本專案的 GitHub URL；不要同時在多個技能目錄安裝同名副本。

在技能目錄中執行以下 Windows PowerShell 指令，建立一次執行環境：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

需要 Python 3.10 以上，以及圖片檢視工具；從 Drive 取檔時還需要 Google Drive 連接器與可下載檔案的網路權限。macOS/Linux 可用 `python3 -m venv .venv`，並使用 `.venv/bin/python`。虛擬環境不包含在本專案中。

## 使用

在對話中輸入 `$goodnotes-pdf-vision`，再指定 PDF、頁碼與要問的問題；例如：請從我提供的 Drive 資料夾找到演算法筆記，解釋實際 PDF 第 7 頁。

已開啟隱式選用：當技能可被探索、agent 確實判定任務符合描述時，可以自行載入，不必每次明確呼叫。這不是每次必定啟動的保證；明確提及技能可提高確定性。agent 讀取並執行技能時知道自己使用了它，且操作說明要求在開始時告知使用者。

## 暫存檔與儲存空間

預設流程：建立本次暫存目錄 → 下載 PDF 副本 → 渲染指定頁面 → 用圖片工具看圖 → 清除本次 PDF/PNG 副本 → 回答。

`temp_workspace.py` 提供建立與清理指令，清理前檢查特定目錄名稱、標記及路徑，拒絕連結或 junction，且不修改使用者的原始 PDF。失敗時保留清理標記以便重試。

```text
python scripts/temp_workspace.py create --work-root <本次工作目錄>
python scripts/temp_workspace.py cleanup --session <create回傳的完整session路徑>
```

單獨執行 `pdf_to_png.py` 是一般匯出功能，會保留輸出。自動清理是 agent 必須執行的完整技能流程，不能在圖片尚未讀取前就刪除它。

正常完成會清除暫存檔，失敗或可恢復取消時也要嘗試清理。強制關閉、斷電或權限變動可能留下檔案，沒有背景清理服務，也不保證安全抹除。已安裝程式、Python 套件、App/OS 快取，以及對話系統保存的圖片不在此清理範圍；不承諾總儲存空間為零。使用者明確要求保存的 PNG 會保留。

## 測試

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

清理測試涵蓋原檔與其他 session 保護、重複清理、非法目錄、標記不符、清理失敗重試及連結拒絕；無法建立連結的系統會跳過連結案例。已在 Windows 驗證真實 PDF 第 7 頁的渲染、圖片讀取與暫存檔刪除。

本公開版本不包含私人 Drive 資料夾 ID、筆記、帳號憑證或臨時下載網址。
