# Handwritten PDF Vision — AI Agent Skill

[繁體中文](README.md) | **English**

Author: [海鮮稽查長 SeaFoodInspector](https://github.com/SeaFoodInspector056)

Version: 1.2.0

An **AI agent skill** using the open [Agent Skills format](https://agentskills.io/home). It retrieves a PDF from Google Drive or a local file, renders selected pages to PNG, and asks a vision-capable agent to actually inspect those images before explaining handwritten notes, formulas, and diagrams. It uses PyMuPDF page rendering rather than replacing the page image with OCR or extracted PDF text.

## Visual analysis of handwritten PDF notes

Use this workflow with note-taking applications that export PDF. It analyzes the exported page images, including handwriting, equations, and layout. Goodnotes is the source tested so far; PDFs exported by other applications can follow the same workflow, but those applications have not been individually tested. Native notebook formats are outside the current scope.


## Better input for handwritten-note recognition

**This skill aims to improve an agent's accuracy when reading and understanding handwritten notes.** Compared with providing only extracted PDF text, page images preserve handwriting, superscripts and subscripts, equation layout, arrows, colors, and spatial context. This gives a vision model more complete evidence to interpret the page and is useful for handwritten PDFs without a usable text layer.

Actual results depend on source legibility, rendering resolution, and the model's capabilities. This project has not conducted a quantitative handwriting-recognition accuracy comparison. Rendering cannot guarantee correct recognition of every mark or recover detail that was already blurred in the source.

## Why Python?

Python handles downloading, page selection, file management, and cleanup. PyMuPDF delegates the actual rendering to the native MuPDF engine, so pixel rendering is not implemented as Python loops. This provides native rendering capabilities without adding a separate C++ build toolchain. See the [PyMuPDF tutorial](https://pymupdf.readthedocs.io/en/latest/tutorial.html).

Resolution, page dimensions, PDF complexity, PNG encoding, and disk I/O are major performance factors. Doubling DPI roughly quadruples the pixel count. Python is a practical choice for maintaining this small, cross-platform workflow; whether a C++ implementation is faster requires measuring the same engine, files, resolution, and hardware.

## Supported agents and compatibility

This project is an **AI Agent Skill**. It has been tested in a local Codex environment on Windows 11. Other Agent Skills-compatible products can reuse the core instructions and Python scripts if they provide:

- Skill discovery/loading, Python execution, and local file access.
- A tool that actually supplies page images to a vision-capable model.
- Authorized original-file retrieval and network access when using Google Drive.

| Environment | Verification status |
| --- | --- |
| Codex, including local Codex in the ChatGPT desktop app, on Windows 11 | Downloading, rendering, image viewing, and scratch cleanup verified |
| Other Agent Skills-compatible agents | Portable format and scripts; tool names, installation paths, and permissions may need adaptation. Not tested |

`agents/openai.yaml` supplies Codex-specific interface and invocation settings. Other products can use their own discovery mechanism with the core `SKILL.md` and scripts. Automatic skill selection depends on the host product. See the [Agent Skills overview](https://agentskills.io/home).

## Installation: Codex example

Install this directory as a discoverable skill named `handwritten-pdf-vision`. With Codex's skill-installer, provide this repository's GitHub URL. Avoid installing duplicate copies under multiple skill locations.

From the skill directory, create the runtime once in Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Requirements: Python 3.10+, an image-viewing tool, and appropriate local permissions. Google Drive use additionally requires a Drive connector and network access for downloads. On macOS/Linux, use `python3 -m venv .venv` and `.venv/bin/python`. The virtual environment is not bundled with the repository.

## Usage

Mention `$handwritten-pdf-vision` in a Codex conversation, then specify the PDF, physical page number, and question. For example: find my algorithm notes in the Drive folder I provide and explain physical PDF page 7. Use the invocation mechanism supported by your host if it differs from Codex.

Implicit invocation is enabled for Codex: an agent can load the skill when it is discoverable and the request matches its description. Automatic selection is not guaranteed; explicitly mentioning the skill makes the intent clear. An agent that loads and executes the skill knows it is using it, and the instructions require it to announce this before starting.

## Temporary files and disk usage

Default workflow: create a per-request scratch directory → download a PDF copy → render selected pages → inspect the images → remove the temporary PDF/PNG copies → answer.

`temp_workspace.py` creates and removes marked scratch sessions. Cleanup checks the directory name, marker, and resolved paths, refuses links/junctions, and preserves the user's original PDF. Its marker is retained when payload removal fails so cleanup can be retried.

```text
python scripts/temp_workspace.py create --work-root <task-work-directory>
python scripts/temp_workspace.py cleanup --session <exact-session-path-returned-by-create>
```

Running `pdf_to_png.py` by itself is a regular export operation and preserves its output. Cleanup belongs to the complete agent workflow and must happen after the agent has viewed the images.

Normal completion removes scratch files; failures and recoverable cancellation must also attempt cleanup. Forced termination, power loss, or changed permissions can leave files behind. There is no background cleanup service or secure-erasure guarantee. Installed code, Python dependencies, app/OS caches, and images retained by the conversation service are outside scratch cleanup. Total disk use is not guaranteed to be zero. PNG exports explicitly requested by the user are preserved.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Cleanup tests cover preservation of originals and other sessions, repeated cleanup, invalid target directories, mismatched markers, retry after failure, and link rejection. The link case is skipped if the OS does not permit creating a test link. Rendering, image inspection, and scratch deletion have also been verified with a real PDF page on Windows.

The public repository contains no private Drive folder IDs, notebooks, account credentials, or temporary download URLs.
