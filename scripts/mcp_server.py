"""Local stdio MCP server: PDF -> in-memory PNG -> MCP ImageContent.

Author: 海鮮稽查長 SeaFoodInspector. Original code licensed under MIT.
No OCR, model API, image files, document cache, or background service.
"""

import base64
from contextlib import contextmanager
import json
import math
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

import pymupdf
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, ImageContent, TextContent, ToolAnnotations
from pydantic import Field

MAX_PDF_BYTES = 100 * 1024 * 1024
MAX_PIXELS = 20_000_000
MAX_IMAGE_BYTES = 8 * 1024 * 1024  # Encoded MCP payload budget, including base64.
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False,
                            idempotentHint=True, openWorldHint=True)
mcp = FastMCP("handwritten-pdf-vision")


def validate_url(url):
    parsed = urlsplit(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("pdf_url must be an HTTPS download URL without embedded credentials.")


class HTTPSRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_bytes(url):
    validate_url(url)
    try:
        request = Request(url, headers={"User-Agent": "handwritten-pdf-vision/2.0"})
        with build_opener(HTTPSRedirects()).open(request, timeout=30) as response:
            length = response.headers.get("Content-Length")
            if length and int(length) > MAX_PDF_BYTES:
                raise ValueError("PDF exceeds the 100 MiB download limit.")
            data = bytearray()
            while True:
                chunk = response.read(min(1024 * 1024, MAX_PDF_BYTES + 1 - len(data)))
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > MAX_PDF_BYTES:
                    raise ValueError("PDF exceeds the 100 MiB download limit.")
        if b"%PDF-" not in data[:1024]:
            raise ValueError("The download is not a PDF; obtain a fresh raw-file download URL.")
        return bytes(data)
    except ValueError:
        raise
    except Exception:
        # Signed URLs are credentials. Do not echo URLs or provider error bodies.
        raise ValueError("PDF download failed. Check access, connection, or fetch a fresh download URL.") from None


@contextmanager
def open_pdf(file_path=None, pdf_url=None, password=None):
    if bool(file_path) == bool(pdf_url):
        raise ValueError("Supply exactly one of file_path or pdf_url.")
    try:
        if pdf_url:
            doc = pymupdf.open(stream=download_bytes(pdf_url), filetype="pdf")
        else:
            path = Path(file_path.strip().strip('\"')).expanduser().resolve()
            if not path.is_file():
                raise ValueError("Local PDF does not exist or is not a file.")
            if path.stat().st_size > MAX_PDF_BYTES:
                raise ValueError("PDF exceeds the 100 MiB input limit.")
            doc = pymupdf.open(path)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Cannot open PDF; the file may be damaged or inaccessible.") from None
    with doc:
        if not doc.is_pdf or doc.page_count == 0:
            raise ValueError("Input must be a nonempty PDF.")
        if doc.needs_pass and (not password or not doc.authenticate(password)):
            raise ValueError("PDF is encrypted; provide a valid password.")
        yield doc


def text_result(value):
    return TextContent(type="text", text=json.dumps(value, ensure_ascii=False))


@mcp.tool(annotations=READ_ONLY)
def pdf_info(file_path: str | None = None, pdf_url: str | None = None,
             password: str | None = None) -> CallToolResult:
    """Read page count and page sizes, without OCR or extracted page text.

    Supply an absolute local file_path OR an authorized HTTPS raw-file pdf_url.
    Drive sharing/view URLs are not raw download URLs. URLs/passwords are not
    retained by this server. Never publish them in replies or public config.
    """
    with open_pdf(file_path, pdf_url, password) as doc:
        sizes = [{"page": i + 1, "width_pt": p.rect.width, "height_pt": p.rect.height}
                 for i, p in enumerate(doc)]
        return CallToolResult(content=[text_result({"page_count": len(doc), "pages": sizes})])


@mcp.tool(annotations=READ_ONLY)
def render_pdf_page(
    page: Annotated[int, Field(ge=1)],
    file_path: str | None = None,
    pdf_url: str | None = None,
    dpi: Annotated[int, Field(ge=36, le=300)] = 200,
    clip: list[float] | None = None,
    password: str | None = None,
) -> CallToolResult:
    """Return ONE rendered PDF page as an actual MCP image block for vision.

    Physical page numbers start at 1. Supply file_path OR a fresh authorized
    HTTPS raw-file pdf_url. Includes visible annotations, vectors, and images.
    Uses RGB/white background. PNG bytes remain in memory; no PNG/PDF is saved.
    Optional clip=[x0,y0,x1,y1] uses page.rect coordinates in PDF points (72/in),
    allowing a readable crop. Limits: 100 MiB PDF, 20M pixels, 8 MiB base64.
    If too large, lower DPI or request a clip. No OCR or model API is called.
    The host must forward the image block to its vision model; a text/base64
    summary is not visual inspection. Source URL/password may enter host logs.
    """
    with open_pdf(file_path, pdf_url, password) as doc:
        if page > len(doc):
            raise ValueError(f"Page must be between 1 and {len(doc)}.")
        pdf_page = doc[page - 1]
        rect = pdf_page.rect
        if clip is not None:
            if len(clip) != 4 or not all(math.isfinite(v) for v in clip):
                raise ValueError("clip must contain four finite coordinates.")
            rect = pymupdf.Rect(clip)
            if rect.is_empty or rect.is_infinite or not pdf_page.rect.contains(rect):
                raise ValueError("clip must be a nonempty rectangle within page bounds.")
        scale = dpi / 72
        # Match the renderer's outward rounding, including offset crops.
        width = math.ceil(rect.x1 * scale) - math.floor(rect.x0 * scale)
        height = math.ceil(rect.y1 * scale) - math.floor(rect.y0 * scale)
        if width * height > MAX_PIXELS:
            raise ValueError("Page exceeds 20M pixels. Lower DPI or request a clip.")
        pix = pdf_page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB,
                                 alpha=False, annots=True, clip=rect)
        png = pix.tobytes("png")
        if 4 * ((len(png) + 2) // 3) > MAX_IMAGE_BYTES:
            raise ValueError("Image exceeds the 8 MiB response budget. Lower DPI or request a clip.")
        meta = {"page": page, "page_count": len(doc), "dpi": dpi,
                "width": pix.width, "height": pix.height, "clip": list(rect),
                "mime_type": "image/png", "image_files_written": 0,
                "route": "MCP image content; inspect the image before answering"}
        return CallToolResult(content=[text_result(meta), ImageContent(
            type="image", data=base64.b64encode(png).decode("ascii"), mimeType="image/png")])


if __name__ == "__main__":
    mcp.run(transport="stdio")
