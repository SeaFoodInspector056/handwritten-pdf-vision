---
name: handwritten-pdf-vision
description: Visually read handwritten PDF notes, formulas, and diagrams from Google Drive or local files. Use the bundled MCP to render requested pages in memory and return real image content to the agent; no OCR or PNG exports are needed for analysis. Not for editing native notebook formats.
license: MIT
metadata:
  version: "2.0.0"
  author: "海鮮稽查長 SeaFoodInspector"
  github: "https://github.com/SeaFoodInspector056"
---

# Handwritten PDF vision

Author: 海鮮稽查長 SeaFoodInspector · https://github.com/SeaFoodInspector056

Announce use of this skill briefly. Automatic selection is allowed when the request matches. This skill supplies workflow instructions; the bundled **stdio MCP server** supplies `pdf_info` and `render_pdf_page`. Tool names may have a host-added server prefix. Its PNG bytes are returned as MCP image content, not saved image files or base64 text for the model to decode. No OCR, external inference API, API key, or cloud renderer is used.

## Setup once per computer

Use the skill's persistent `.venv/Scripts/python.exe` on Windows or `.venv/bin/python` elsewhere. If missing, create a Python 3.10+ venv here and install `requirements.txt`. Do not copy a venv between machines or reinstall each invocation.

For Codex, run `scripts/setup_mcp.py --register-codex` with that interpreter. It registers this installation's server and refuses to replace a different same-name registration. Reload MCP connections or restart the app if tools are not visible. For other hosts, `scripts/setup_mcp.py` prints the equivalent stdio configuration. The host must support MCP image blocks and a vision-capable model. Skill installation alone does not register MCP or grant permissions.

If the tool remains unavailable, explain the missing connection. Do not silently revert to OCR, extracted text, or the v1 disk-image workflow and call it MCP success. A protocol test can verify the server, but is distinct from the host discovering and calling it directly.

## Obtain the current source

Read [references/sources.md](references/sources.md) when source discovery is needed. For a local PDF, pass its absolute `file_path`; never alter the original. For Google Drive, discover the connector and verify the target's name, PDF MIME type, size, and modification time. Request the **original file** with `download_raw_file=true, include_base64=false`.

- If the connector supplies an authenticated HTTPS `file_uri.download_url`, pass it as `pdf_url` to MCP. Do not reconstruct URLs or use a Drive `/view` link as a download URL. The MCP reads the PDF into memory and discards it after each call; no PDF copy is written by the server.
- If it supplies only a materialized local path, pass `file_path`. Connector-owned downloads and caches are outside this server's control; do not delete them as owned scratch files.
- Use the current revision for Drive requests. On expiry, fetch a fresh download URL once; on repeated failure report the failing stage. Do not change sharing or global access settings. Never publish signed URLs, passwords, credentials, or private source IDs in public files. Tool arguments may be retained by the host, even though the server does not persist them.

## Render and inspect

Call `render_pdf_page(page=7, pdf_url=<authorized-download-url>, dpi=200)` or use `file_path`. Page numbers are physical PDF order starting at 1. Use `pdf_info` only if page count or geometry is needed; it does not extract page text. Each render returns one page, metadata, and an `image/png` MCP image block. For several pages, call separately in small batches. Clarify scope before an unbounded whole-notebook request.

Actually inspect the returned image before explaining handwriting. A successful download, metadata response, base64 string, or text summary is not visual inspection. If the host hides images from the model, report that limitation rather than claiming to have seen them. Preserve equations, arrows, colors and spatial relationships; mark uncertain symbols.

Start at 200 DPI. Use up to 300 DPI or a `clip=[x0,y0,x1,y1]` in page-rectangle coordinates (PDF points, 72/inch) for small handwriting. Limits are 100 MiB PDF, 20 million pixels, and 8 MiB base64 image payload per call. If a limit is hit, lower DPI or render a crop; never silently omit pages. Large notebooks may need local source access or explicit splitting outside this server.

Answer in the user's language, cite source PDF name/URL and physical page, and briefly state that MCP images were inspected. Report actual evidence only: server/protocol checks, host integration, and visual analysis are different validation levels.

## Storage and legacy migration

The v2 server writes no PDF/PNG copies, keeps no cross-request document cache, and closes each PDF after its call. It does not guarantee zero total disk use: dependencies, host logs/images, OS paging, downloads owned by the connector, and caches are outside its control. It has no background service or janitor. If a user explicitly requests saved images, the retained legacy `scripts/pdf_to_png.py` can export them; this is a separate export operation with persistent output, not the default MCP analysis route. `download_pdf.py` and `temp_workspace.py` remain only for compatibility with known v1 sessions and manual exports. Do not sweep unrelated directories.

Original code and instructions use [MIT](LICENSE); dependencies retain their own licenses, including PyMuPDF/MuPDF's separate terms in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
