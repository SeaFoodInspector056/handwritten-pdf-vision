---
name: handwritten-pdf-vision
description: Read and explain handwritten PDF notes exported from note-taking applications from Google Drive or a local file by rendering requested pages to PNG and actually viewing them, then cleaning per-request scratch files. Use for handwritten notes, formulas, diagrams, and page-specific visual analysis; not for editing native notebook formats. Goodnotes is the source tested so far.
metadata:
  version: "1.2.0"
  author: "海鮮稽查長 SeaFoodInspector"
  github: "https://github.com/SeaFoodInspector056"
---

# Handwritten PDF vision

Author: 海鮮稽查長 SeaFoodInspector · https://github.com/SeaFoodInspector056

Use this skill proactively when a request matches its description; explicit invocation is optional. Briefly tell the user you are using the Handwritten PDF vision skill before rendering. If asked whether you used it, distinguish reading this SKILL.md, running its bundled scripts, and actually viewing images. Never claim activation or successful cleanup without doing it.

Use the renderer bundled in `scripts/pdf_to_png.py`; do not download a renderer from Drive or G:. Render locally with PyMuPDF. Do not substitute OCR, extracted PDF text, or connector summaries for looking at the page image.

## Runtime

Let `<skill>` be this SKILL.md's directory. Use its persistent `.venv/Scripts/python.exe` on Windows, or `.venv/bin/python` elsewhere. If missing, use an available Python 3.10+ to create this venv and install `requirements.txt` once. Do not reinstall packages or copy another computer's venv on every invocation. A skill does not grant filesystem or network permissions.

## Per-request scratch lifecycle

Default to temporary images, not persistent exports. With the skill's Python interpreter run:

```text
scripts/temp_workspace.py create --work-root <current-task-work-directory>
```

This returns a unique `session` directory, `pdf` download path, and `images` output root. Keep these values. Save only newly downloaded copies, rendered PNGs, and crops in this directory. Do not move an original local PDF into it.

Plan the whole operation as try/finally: obtain PDF, render, view images, then call the cleanup command before the final reply. Do this on normal completion, download/render/view failures, and recoverable cancellation. Cleanup is a separate required tool action after viewing; rendering alone cannot know when an agent has finished reading a PNG.

```text
scripts/temp_workspace.py cleanup --session <exact-session-path-returned-by-create>
```

The helper verifies the directory name, path, session marker, and absence of links/junctions before removal. It deletes only that session's payloads and verifies that the session is gone. Repeat on the same exact path if necessary; cleanup is idempotent. If cleanup fails, report the retained path and failure without claiming zero storage. Do not sweep arbitrary temp folders or delete another active request's session. A known interrupted session in the same task can be cleaned after confirming it is no longer in use.

Crashes, forced termination, lost filesystem permissions, and sudden power loss can leave temporary files. There is no background janitor or secure-erasure guarantee. The installed skill, runtime dependencies, app/OS caches, and image content retained by the conversation are outside this scratch cleanup. Never promise zero total disk use or deletion from chat/service storage.

If the user explicitly requests saved PNGs, copy those requested exports to the task's deliverable directory before cleanup and explain that the saved exports will persist. Do not provide a local scratch-image link after deleting its target.

## Obtain the current PDF

- Read [references/sources.md](references/sources.md) for source-discovery context. Search/list the user's supplied folder when a file is unknown; resolve ambiguous names. Verify MIME type, size and modification time. Choose the exported PDF, not a native notebook archive such as `.goodnotes`.
- For Drive, discover the available connector tools. Fetch the original with `download_raw_file=true`, `include_base64=false`, using previously verified file metadata. Prefer a materialized local path; otherwise use the authenticated top-level `file_uri.download_url`. Do not reconstruct or publish signed URLs.
- Run `scripts/download_pdf.py --output <session-pdf-path> --expected-bytes <metadata-size>` and pass the returned HTTPS URL as its single stdin line. Omit expected size if genuinely unavailable. It streams chunks, checks the PDF header/size, and refuses to overwrite an existing file. Connector-materialized originals belong to the connector; do not delete them as if they were this skill's copies.
- Local user-supplied PDFs may be read directly and must remain untouched. For Drive requests, obtain the current revision instead of silently using an old local copy. G: is optional; verify access and synchronization if the user chooses it.
- Report blocked network/filesystem access at the exact failing stage. Do not change global permissions or sharing settings.

## Render, view, clean, explain

Run with the skill's interpreter:

```text
scripts/pdf_to_png.py <pdf-path> --pages 7 --dpi 200 --output <session-images-root>
```

Page numbers are physical PDF order starting at 1, not handwritten/custom labels. Accept one page, `1,3-5`, or `all`. Render only the needed pages. Clarify a large request with no page scope; for large selections use small batches and remove already-viewed PNGs inside the owned scratch session before rendering further batches. Start at 200 DPI; use 300 if small handwriting needs it. The renderer includes visible annotations, RGB, a white background, page-bound checks, and a pixel budget.

Actually open every image used as evidence with the image-viewing tool. Preserve formulas, arrows, annotations, and layout in the explanation; flag unreadable symbols. After viewing all needed images and checking your reading, clean the session before answering. A follow-up requiring another look should render again rather than rely on a nonexistent image file.

Answer in the user's language and cite the source PDF URL/name and physical page. Briefly confirm skill use and temporary-file cleanup when successful. Only say full verification succeeded if obtaining the file, rendering, viewing, and cleanup all succeeded. Do not upload images to Drive unless asked.
