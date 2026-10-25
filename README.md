# Handwritten PDF Vision — AI Agent Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Version: 1.2.1](https://img.shields.io/badge/Version-1.2.1-2563EB?style=flat-square)](SKILL.md)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![PyMuPDF: 1.28.2](https://img.shields.io/badge/PyMuPDF-1.28.2-16A34A?style=flat-square)](requirements.txt)

**繁體中文** | [English](README.en.md)

作者：[海鮮稽查長 SeaFoodInspector](https://github.com/SeaFoodInspector056)

版本：1.2.1

一個採用 [Agent Skills 開放格式](https://agentskills.io/home)的 **AI agent 技能**，適用於具備技能載入、程式執行與圖片檢視能力的 agent：從 Google Drive 、 NAS 、本機等地取得 PDF 後，將指定頁面渲染為 PNG，讓 agent 使用視覺模型查看圖檔後，分析解釋手寫筆記、公式與圖形，而非直接使用 PDF 抽取文字字串來讀取手寫字跡，以提高手寫筆記的分析準確度。

## 省流：這個 skill 解決什麼？

**解決「agent 讀到了 PDF 的文字，卻沒有真正看到筆記頁面」的輸入流程問題。** 在本專案的 Google Drive 連接器測試中，預設讀取回傳的是文字；它可以支援摘要，但不足以證明 agent 看過手寫筆跡、圖像、箭頭或版面，手寫內容也可能出現辨識錯誤。

- **一般文字讀取路徑**：Drive PDF → 連接器提供文字 → agent 根據文字回答。
- **本技能的明確看圖路徑**：取得原始 PDF → 渲染指定頁面為 PNG → agent 實際看圖 → 清除本次暫存副本。
- **適合使用時機**：現有取檔工具只提供文字，或需要明確控制頁碼、解析度與暫存清理時。

這不是所有 agent／PDF 功能的通則，也不是 PNG 天生比 PDF 準。若平台已能將 PDF 頁面影像提供給視覺模型，可以直接使用那條路徑，不必先自行轉成 PNG。以 OpenAI Responses API 為例，支援視覺的模型接收 PDF `input_file` 時會取得文字與頁面影像；但把 Drive 回傳的文字交給模型，或只下載 PDF 到本機，不等於已把原始 PDF 接入這種視覺輸入。[官方文件](https://developers.openai.com/api/docs/guides/file-inputs)，因此最簡單的方法就是像平常截圖一樣把圖片直接給 agent 去視覺讀取分析。

## 手寫筆記 PDF 看圖分析

適用於能匯出 PDF 的筆記軟體：本技能處理匯出的 PDF 頁面，讓 agent 看圖分析手寫字、公式與版面。Goodnotes 是目前已實測的來源；其他軟體匯出的 PDF 可使用相同流程，但尚未逐一實測。筆記軟體的專用檔案格式不在目前支援範圍內。


## 改善手寫筆記的辨識

**這個技能以提升 agent 辨識與理解手寫筆記的準確度為目標。** 相較於只提供 PDF 抽取文字，頁面圖片保留筆跡、上下標、公式排列、箭頭、顏色與上下文位置，讓視覺模型有更完整的依據判讀內容，也適合處理缺少可用文字層的手寫 PDF。


## 為什麼選擇 Python？

Python 負責下載、頁碼選擇、輸出管理與清理；實際渲染則由 PyMuPDF 呼叫原生 MuPDF 引擎完成。因此，這個流程不會把逐像素繪圖工作放在 Python 迴圈中，也不必為了使用原生渲染效能另外維護 C++ 建置環境。[PyMuPDF 官方說明](https://pymupdf.readthedocs.io/en/latest/tutorial.html)

效能主要受到解析度、頁面大小、PDF 內容複雜度、PNG 編碼與磁碟 I/O 影響。DPI 加倍會讓像素數約增加為四倍。對這種指定頁面的工具，Python 的開發、維護與跨平台便利性很合適；換成 C++ 是否更快，仍要用相同引擎、檔案、解析度與硬體實測。

## 適用的 AI agent

本專案是 **AI Agent Skill**；目前已在 Windows 11 的 Codex 執行環境完成實測。`SKILL.md` 與 Python 程式可供其他支援 Agent Skills 的產品沿用，但該產品必須提供以下能力：

- 載入 `SKILL.md`，執行 Python 並讀寫本機檔案。
- 實際開啟頁面圖片，將圖片提供給具備視覺能力的模型。
- 若使用 Google Drive，能授權取得原始 PDF，並允許下載檔案。

| 執行環境 | 驗證狀態 |
| --- | --- |
| Codex／ChatGPT 桌面應用程式中的本機 Codex，Windows 11 | 已驗證下載、渲染、圖片讀取與暫存清理 |
| 其他支援 Agent Skills 的 agent | 格式與程式可沿用；工具名稱、安裝位置與權限可能需要調整，尚未實測 |

`agents/openai.yaml` 提供 Codex 介面與選用設定；其他產品可依自己的技能探索機制使用核心 `SKILL.md` 與程式。技能是否能自動選用，也由各產品決定。[Agent Skills 格式說明](https://agentskills.io/home)

## 快速安裝

### 方法一：支援的 AI agent 通用安裝指令

電腦需先有 Node.js 與 `npx`；在終端機執行：

```bash
npx skills add SeaFoodInspector056/handwritten-pdf-vision --skill handwritten-pdf-vision
```

依安裝工具提示選擇要使用的 agent 與安裝範圍。這會安裝技能指令及程式，不會替你登入 Google Drive，也不包含 Python 套件。首次使用時，agent 可依 `SKILL.md` 建立 Python 執行環境。

只查看 Repo 是否能找到技能、不安裝：

```bash
npx skills add SeaFoodInspector056/handwritten-pdf-vision --list
```

此 Repo 已通過 Skills CLI 的 `--list` 探索檢查，會列出 `handwritten-pdf-vision`。這不等於已在所有 agent 實測，也不代表已取得 skills.sh 目錄收錄或審核。[Skills CLI 官方說明](https://skills.sh/docs/cli)

### 方法二：直接請 Codex 安裝

將以下要求交給有 skill-installer 的 Codex：

> 請用 skill-installer 安裝 https://github.com/SeaFoodInspector056/handwritten-pdf-vision 。技能位於 Repo 根目錄，安裝名稱為 handwritten-pdf-vision；請保留已有的私人來源設定，並準備 Python 執行環境。

### 方法三：手動安裝與 Python 環境


將本資料夾安裝為 Codex 可探索到的 `handwritten-pdf-vision` 技能資料夾。若使用 Codex 的 skill-installer，可提供本專案的 GitHub URL；不要同時在多個技能目錄安裝同名副本。

在技能目錄中執行以下 Windows PowerShell 指令，建立一次執行環境：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

需要 Python 3.10 以上，以及圖片檢視工具；從 Drive 取檔時還需要 Google Drive 連接器與可下載檔案的網路權限。macOS/Linux 可用 `python3 -m venv .venv`，並使用 `.venv/bin/python`。虛擬環境不包含在本專案中。

## 使用

在對話中輸入 `$handwritten-pdf-vision`，再指定 PDF、頁碼與要問的問題；例如：請從我提供的 Drive 資料夾找到演算法筆記，解釋實際 PDF 第 7 頁。

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

## 授權

本專案原創的技能指令、程式與文件採用 [MIT License](LICENSE)，作者為海鮮稽查長 SeaFoodInspector。允許使用、修改、散布及商用，並須保留著作權與授權聲明。

PyMuPDF/MuPDF 採用另外的 AGPL／商業授權；本專案的 MIT 不會取代依賴套件的條款。整合散布或部署時須另外評估適用義務，詳見 [第三方依賴授權](THIRD_PARTY_NOTICES.md)。
