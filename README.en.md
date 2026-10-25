# Handwritten PDF Vision — AI Agent Skill + MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Version: 2.0.0](https://img.shields.io/badge/Version-2.0.0-2563EB?style=flat-square)](SKILL.md)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![PyMuPDF: 1.28.2](https://img.shields.io/badge/PyMuPDF-1.28.2-16A34A?style=flat-square)](requirements.txt)
[![MCP: 1.30.0](https://img.shields.io/badge/MCP_SDK-1.30.0-555555?style=flat-square)](requirements.txt)

[繁體中文](README.md) | **English**

Author: [海鮮稽查長 SeaFoodInspector](https://github.com/SeaFoodInspector056)

## TL;DR: what problem does this skill solve?

**Who this is especially useful for**:

People who find it inconvenient to take and upload screenshots of handwritten notes every time they want AI analysis, dislike the space those screenshots take up in their photo library, and want an agent to read their handwritten digital notes in PDF format **without taking screenshots**.

---

**Help prevent agents from misinterpreting handwritten PDF content when reading files directly**:

Because most Drive/PDF tools return only text strings by default, handwriting, equation layout, arrows, colors, and images are lost in the process. This project therefore combines [Agent Skills](https://agentskills.io/home) instructions with a local MCP renderer to supply the complete requested page to the current agent's vision model for analysis of handwritten notes, formulas, and diagrams. Just like handing the agent a screenshot, this lets it actually see the handwritten PDF page and can help **substantially improve analysis accuracy**.

---

**Supports PDFs from Google Drive, NAS, and local storage** (NAS must first be mounted as a readable local file path).

```text
Authorized original-PDF download URL / local PDF
    → MCP reads and renders the requested page in memory
    → returns actual MCP image content
    → agent inspects the image and explains the notes
```

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

## Verification

From the skill directory:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Tests include real stdio MCP initialization, tool discovery, image and error responses, page bounds, cropping, encrypted PDFs, download limits, no image files written, and original-file preservation. Page 10 of a notebook also completed Drive → memory → MCP image result → display and actual visual inspection. That run forwarded the image through a test MCP client; native host discovery/calling after reloading is a separate integration check. Other clients have not been individually tested.

## License

Original code, skill instructions, and documentation use [MIT](LICENSE), attributed to 海鮮稽查長 SeaFoodInspector. The MCP Python SDK is MIT; PyMuPDF/MuPDF retain separate AGPL/commercial licensing, which this project's MIT license does not replace. See [third-party notices](THIRD_PARTY_NOTICES.md). The public repository contains no private notebooks, Drive IDs, credentials, or temporary download URLs.
