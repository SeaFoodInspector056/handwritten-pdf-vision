# Handwritten PDF Vision — AI Agent Skill + MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Version: 2.0.0](https://img.shields.io/badge/Version-2.0.0-2563EB?style=flat-square)](SKILL.md)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![PyMuPDF: 1.28.2](https://img.shields.io/badge/PyMuPDF-1.28.2-16A34A?style=flat-square)](requirements.txt)
[![MCP: 1.30.0](https://img.shields.io/badge/MCP_SDK-1.30.0-555555?style=flat-square)](requirements.txt)

[繁體中文](README.md) | **English**

Author: [海鮮稽查長 SeaFoodInspector](https://github.com/SeaFoodInspector056)

## TL;DR for AI agents

**Let the agent actually see handwritten PDF pages instead of receiving only extracted text.** Some Drive/PDF tools default to text, losing handwriting, equation layout, arrows, colors, and diagrams. This project combines [Agent Skills](https://agentskills.io/home) instructions with a local MCP renderer that supplies page images to the current agent's vision model.

Sources can include Google Drive, NAS, and local files. Mount NAS storage as a readable local file path first. Like handing the agent a screenshot, the tool automatically supplies the requested page image so the vision model can analyze handwriting, formulas, and diagrams with more complete evidence.

```text
Authorized original-PDF download URL from Drive / local PDF
    → MCP reads and renders the requested page in memory
    → returns actual MCP image content
    → agent inspects the image and explains the notes
```

**Version 2.0 does not create temporary PDF/PNG copies by default.** Images are still PNG-encoded, but returned as memory data instead of being saved, opened, and deleted. If the connector only provides a local download, the server reads that file; connector-owned copies remain the connector's responsibility.

This is not a universal limitation of agents or PDFs, and PNG is not inherently more accurate than PDF. Hosts with complete PDF visual input can use that route. This project provides an explicit MCP route with page and resolution control. It makes no separate model API calls and needs no API key; the conversation host's normal usage rules still apply.

## Scope and handwriting recognition

Works with PDFs exported from Goodnotes or other note-taking applications, including handwriting, formulas, diagrams, and annotations. Goodnotes exports have been used in testing; other applications have not been individually tested. Native notebook formats such as `.goodnotes` are outside scope.

Compared with extracted text alone, full page images provide more complete evidence, **aiming to improve handwritten-note recognition and understanding**.

## Install both the skill and MCP

Requires Python 3.10+, an agent that can run local stdio MCP servers, and a client that forwards MCP image content to a vision-capable model. Drive sources also need an authorized Drive connector. No Drive credentials are bundled.

1. Install the skill. With Node.js/npx available:

   ```bash
   npx skills add SeaFoodInspector056/handwritten-pdf-vision --skill handwritten-pdf-vision
   ```

   Alternatively, ask Codex's skill-installer to install this repository's root skill and preserve existing private source settings.

2. Open Windows PowerShell or the VS Code terminal **in the installed skill directory** and set up the runtime once:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe scripts/setup_mcp.py --register-codex
   ```

   Codex CLI must be available in the terminal. The helper adds only this project's MCP registration and refuses to replace an existing same-name registration pointing elsewhere. Do not recreate an existing venv unnecessarily.

3. Reload MCP connections or restart the application and confirm `pdf_info` and `render_pdf_page` are available. **Installing SKILL.md alone does not connect MCP.**

On macOS/Linux, use `python3 -m venv .venv` and `.venv/bin/python`. For other clients, run `python scripts/setup_mcp.py` to print stdio JSON containing the actual absolute paths, then add it through that client's configuration. Recreate the runtime and registration on each computer; do not copy venvs or another computer's absolute paths.

See [official Codex MCP configuration](https://learn.chatgpt.com/docs/extend/mcp). Skills CLI installs the skill, not Drive authentication or MCP registration, and does not prove compatibility with every agent.

## Usage

Ask your agent:

> Use $handwritten-pdf-vision to find my computer networking notes in Drive and analyze physical PDF page 10.

Implicit invocation remains enabled, but selection depends on the agent. Explicit invocation makes the intent clear. The agent should announce skill use and actually inspect the image before answering.

| MCP tool | Purpose |
| --- | --- |
| `pdf_info` | Page count and geometry, without extracting notebook text |
| `render_pdf_page` | One page as metadata plus an actual `image/png` MCP content block |

Supply exactly one of `file_path` or `pdf_url`. The URL must be the connector's authorized HTTPS **original-file download URL**, not a Drive `/view` sharing link. Refresh expired URLs and never publish signed URLs. Page numbers start at 1 in physical PDF order, independent of handwritten labels.

Default resolution is 200 DPI, configurable from 36–300 DPI. For small handwriting, increase DPI or use `clip=[x0,y0,x1,y1]` in `page.rect` coordinates, measured in PDF points (72 per inch). Each call returns one page; request multiple pages in separate calls.

Per-call limits: 100 MiB PDF, 20 million pixels, and 8 MiB base64 image data. Exceeding a limit produces an error: reduce DPI or use a crop. Pages are not silently omitted. Large PDFs may need splitting elsewhere. Remote PDFs are fetched anew each call to avoid cross-request document caching; a local original can reduce downloads when reading many pages.

## Storage and migration from 1.x

The v2 MCP writes no PDF/PNG copies, leaves originals untouched, and retains no cross-request document cache. Installed code, dependencies, conversation images, tool-argument logs, connector/app caches, and OS paging are outside this guarantee. Total disk use is not zero. The server does not log download URLs or passwords, but the host may retain tool arguments.

When upgrading from 1.x, preserve private `references/sources.md` and the local runtime, install the added dependency, and register MCP. The legacy `pdf_to_png.py` remains available for **explicit persistent image exports**. `download_pdf.py` and `temp_workspace.py` remain for legacy compatibility and cleanup of known old sessions. They are no longer the default analysis route.

## Verification

From the skill directory:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Tests include real stdio MCP initialization, tool discovery, image and error responses, page bounds, cropping, encrypted PDFs, download limits, no image files written, and original-file preservation. A Goodnotes networking notebook's page 10 also completed Drive → memory → MCP image result → display and actual visual inspection. That run forwarded the image through a test MCP client; native host discovery/calling after reloading is a separate integration check. Other clients have not been individually tested.

## Why Python?

Python handles MCP, downloads, and parameters. PyMuPDF delegates rendering to the native MuPDF engine. Resolution, PDF complexity, image encoding, and transfer remain the major costs; switching to C++ does not automatically improve performance. This revision removes default PDF/PNG disk writes; rendering and visual processing still occur.

## License

Original code, skill instructions, and documentation use [MIT](LICENSE), attributed to 海鮮稽查長 SeaFoodInspector. The MCP Python SDK is MIT; PyMuPDF/MuPDF retain separate AGPL/commercial licensing, which this project's MIT license does not replace. See [third-party notices](THIRD_PARTY_NOTICES.md). The public repository contains no private notebooks, Drive IDs, credentials, or temporary download URLs.
