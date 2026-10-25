# Handwritten PDF Vision — AI Agent Skill + MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Version: 2.0.0](https://img.shields.io/badge/Version-2.0.0-2563EB?style=flat-square)](SKILL.md)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![PyMuPDF: 1.28.2](https://img.shields.io/badge/PyMuPDF-1.28.2-16A34A?style=flat-square)](requirements.txt)
[![MCP: 1.30.0](https://img.shields.io/badge/MCP_SDK-1.30.0-555555?style=flat-square)](requirements.txt)

**繁體中文** | [English](README.en.md)

作者：[海鮮稽查長 SeaFoodInspector](https://github.com/SeaFoodInspector056)

## 省流：這個 skill 解決什麼？

**特別適用客群** ：

覺得每次都要把手寫筆記截圖一次並傳給 AI 分析很麻煩且佔用相簿空間，因此想讓 agent **不需要截圖**就直接讀取使用手寫電子筆記 pdf 檔案的人。

---

**就像平常把截圖交給 agent 看一樣，讓 agent 真正看到手寫 PDF 的頁面，而不是只收到抽取文字** ：

部分 Drive／PDF 工具預設只回傳文字，可能遺失手寫筆跡、公式排版、箭頭、顏色與圖像。這個專案結合 [Agent Skills](https://agentskills.io/home) 指令與本機 MCP 渲染工具，將指定頁面的完整畫面交給目前 agent 的視覺模型分析手寫筆記、公式與圖形，以**改善分析準確度**。

---

**支援從 Google Drive、NAS、本機等來源取得 PDF** （NAS 需先掛載為本機可讀取的檔案路徑）

```text
原始 PDF 的授權下載網址／本機 PDF
    → MCP 在記憶體中讀取與渲染指定頁面
    → 直接回傳 MCP 圖片內容
    → agent 實際看圖後分析
```


## 安裝：技能與 MCP 都要設定

需要 Python 3.10+、可執行本機 stdio MCP 的 agent，以及會把 MCP 圖片內容交給視覺模型的客戶端。Drive 來源另外需要已授權的 Drive 連接器；本專案不包含 Drive 登入憑證。

1. 安裝技能。有 Node.js／npx 時可執行：

   ```bash
   npx skills add SeaFoodInspector056/handwritten-pdf-vision --skill handwritten-pdf-vision
   ```

   也可以請 Codex 使用 skill-installer 安裝本 Repo 根目錄的技能，保留已有私人來源設定。

2. 在**安裝後的技能資料夾**開啟 Windows PowerShell／VS Code 終端機，建立一次環境：

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe scripts/setup_mcp.py --register-codex
   ```

   需要 Codex CLI 可在終端機中呼叫。設定只新增本專案的 MCP；若已有不同路徑的同名設定，會停止要求先檢查。已有 `.venv` 時不必重建。

3. 重新載入 MCP 連線或重開應用程式，確認可呼叫 `pdf_info` 與 `render_pdf_page`。**安裝 SKILL.md 不代表 MCP 已接上。**

macOS／Linux 使用 `python3 -m venv .venv` 與 `.venv/bin/python`。其他 MCP 客戶端可執行 `python scripts/setup_mcp.py`，取得含實際絕對路徑的 stdio JSON 設定，再依該客戶端方式加入。虛擬環境與跨電腦的絕對路徑設定不能直接複製，需在目的電腦重新設定。

Codex 設定參考：[官方 MCP 文件](https://learn.chatgpt.com/docs/extend/mcp)。Skills CLI 只安裝技能，不會自動登入 Drive 或註冊 MCP，也不代表所有 agent 都已相容。

## 使用方式

在對話中說：

> 使用 $handwritten-pdf-vision，從我的 Drive 找到計網概筆記，分析 PDF 第 10 頁。

技能保留自動選用設定，但實際是否選中由 agent 決定，明確提及可提高確定性。agent 應在使用時告知，並實際查看 MCP 圖片才回答。

| MCP 工具 | 功能 |
| --- | --- |
| `pdf_info` | 查看頁數與頁面大小，不抽取筆記文字 |
| `render_pdf_page` | 渲染單一指定頁面，回傳說明文字與真正的 `image/png` MCP 圖片區塊 |

傳入 `file_path` 或 `pdf_url` 其中一個；後者是 Drive 連接器提供的授權 HTTPS **原始檔下載網址**，不是 `/view` 分享網址。網址過期就重新取檔，不公開簽名網址。頁碼從 1 開始，按 PDF 實體頁序，不按手寫頁碼。

預設 200 DPI，可用 36–300 DPI。小字可提高 DPI，或傳入 `clip=[x0,y0,x1,y1]` 裁切區域，座標依 `page.rect`，單位為 PDF 點（72 點／英吋）。每次一頁，多頁分次呼叫。

每次限制：PDF 100 MiB、2,000 萬像素、Base64 圖片資料 8 MiB。超過會明確報錯，請降低 DPI 或裁切；不會默默省略。大型 PDF 可能需要另行分割。遠端 PDF 每次呼叫重新讀取，換取無跨請求快取，處理很多頁時使用本機原檔可減少下載。


## 驗證

在技能資料夾執行：

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

測試包含真正的 stdio MCP 握手、工具探索、圖片回傳與錯誤回傳，以及頁碼、裁切、加密 PDF、下載限制、不產生圖片檔和原檔保護。另以筆記第 10 頁完成 Drive → 記憶體 → MCP 圖片回傳 → 圖片顯示與實際查看；本次透過 MCP 測試客戶端轉交圖片，與應用程式重新載入後的原生工具呼叫分開驗證。其他客戶端未逐一實測。


## 授權

原創程式、技能與文件採用 [MIT](LICENSE)，作者為海鮮稽查長 SeaFoodInspector。MCP Python SDK 為 MIT；PyMuPDF／MuPDF 另有 AGPL／商業授權，依賴條款不會被本專案 MIT 取代。詳見 [第三方依賴說明](THIRD_PARTY_NOTICES.md)。公開 Repo 不包含私人筆記、Drive IDs、憑證或暫時下載網址。
