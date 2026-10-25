"""Behavioral tests, including a real stdio MCP client/server round trip."""

import base64
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

import pymupdf
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import mcp_server as server


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "手寫筆記.pdf"
        with pymupdf.open() as doc:
            page = doc.new_page(width=200, height=300)
            page.insert_text((20, 30), "Visual page 1")
            page.draw_line((20, 40), (180, 140), color=(1, 0, 0), width=3)
            page.add_rect_annot(pymupdf.Rect(20, 160, 100, 220)).update()
            doc.new_page(width=100, height=100).insert_text((10, 20), "Page 2")
            doc.save(self.path)
        self.original = self.path.read_bytes()

    def test_image_content_dimensions_and_no_files_written(self):
        before = set(Path(self.temp.name).rglob("*"))
        result = server.render_pdf_page(page=1, file_path=str(self.path), dpi=144)
        block = result.content[1]
        self.assertEqual((block.type, block.mimeType), ("image", "image/png"))
        png = base64.b64decode(block.data)
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", png[16:24]), (400, 600))
        with pymupdf.open(self.path) as doc:
            expected = doc[0].get_pixmap(dpi=144, colorspace=pymupdf.csRGB,
                                         alpha=False, annots=True).tobytes("png")
            self.assertEqual(png, expected)
        self.assertEqual(before, set(Path(self.temp.name).rglob("*")))
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_page_selection_and_clip(self):
        result = server.render_pdf_page(page=2, file_path=str(self.path), dpi=72,
                                        clip=[0, 0, 50, 50])
        self.assertEqual(json.loads(result.content[0].text)["width"], 50)
        for kwargs in ({"page": 3}, {"page": 1, "clip": [0, 0, 999, 999]},
                       {"page": 1, "clip": [0, 0, float("nan"), 20]}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                server.render_pdf_page(file_path=str(self.path), **kwargs)

    def test_size_budgets_and_source_validation(self):
        with patch.object(server, "MAX_PIXELS", 10), self.assertRaises(ValueError):
            server.render_pdf_page(page=1, file_path=str(self.path))
        with patch.object(server, "MAX_IMAGE_BYTES", 10), self.assertRaises(ValueError):
            server.render_pdf_page(page=1, file_path=str(self.path))
        with self.assertRaises(ValueError):
            server.pdf_info()
        with self.assertRaises(ValueError):
            server.pdf_info(file_path=str(self.path), pdf_url="https://example.org/file.pdf")
        with self.assertRaises(ValueError):
            server.pdf_info(file_path=str(self.path.with_suffix(".missing")))
        for url in ("http://example.org/a.pdf", "https://user:secret@example.org/a.pdf"):
            with self.assertRaises(ValueError):
                server.download_bytes(url)

    def test_download_limits_bad_content_and_private_errors(self):
        response = io.BytesIO(self.original)
        response.headers = {}
        with patch.object(server, "build_opener") as opener:
            opener.return_value.open.return_value = response
            result = server.render_pdf_page(page=1, pdf_url="https://example.org/private?secret=x")
            self.assertEqual(result.content[1].type, "image")
        with patch.object(server, "build_opener") as opener:
            response = io.BytesIO(b"<html>Login required</html>")
            response.headers = {}
            opener.return_value.open.return_value = response
            with self.assertRaisesRegex(ValueError, "not a PDF"):
                server.download_bytes("https://example.org/private")
        with patch.object(server, "build_opener") as opener:
            response = io.BytesIO(self.original)
            response.headers = {}
            opener.return_value.open.return_value = response
            with patch.object(server, "MAX_PDF_BYTES", 10), self.assertRaisesRegex(ValueError, "limit"):
                server.download_bytes("https://example.org/private")
        with patch.object(server, "build_opener", side_effect=OSError("secret-url")):
            with self.assertRaises(ValueError) as error:
                server.download_bytes("https://example.org/private?token=secret")
            self.assertNotIn("secret", str(error.exception))

    def test_encrypted_pdf(self):
        encrypted = Path(self.temp.name) / "locked.pdf"
        with pymupdf.open(self.path) as doc:
            doc.save(encrypted, encryption=pymupdf.PDF_ENCRYPT_AES_256,
                     owner_pw="owner", user_pw="reader")
        with self.assertRaisesRegex(ValueError, "encrypted"):
            server.render_pdf_page(page=1, file_path=str(encrypted))
        result = server.render_pdf_page(page=1, file_path=str(encrypted), password="reader")
        self.assertEqual(result.content[1].type, "image")


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_stdio_tool_discovery_render_and_error(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / "protocol.pdf"
            with pymupdf.open() as doc:
                doc.new_page(width=100, height=100).insert_text((10, 20), "MCP image")
                doc.save(pdf)
            params = StdioServerParameters(command=sys.executable,
                                            args=["-B", str(SCRIPTS / "mcp_server.py")])
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as client:
                    await client.initialize()
                    tools = await client.list_tools()
                    self.assertEqual({t.name for t in tools.tools}, {"pdf_info", "render_pdf_page"})
                    result = await client.call_tool("render_pdf_page", {"page": 1, "file_path": str(pdf)})
                    self.assertFalse(result.isError)
                    self.assertEqual(result.content[1].type, "image")
                    self.assertIsNone(result.structuredContent)
                    error = await client.call_tool("render_pdf_page", {"page": 99, "file_path": str(pdf)})
                    self.assertTrue(error.isError)
                    invalid = await client.call_tool("render_pdf_page", {"page": 0, "file_path": str(pdf)})
                    self.assertTrue(invalid.isError)
            self.assertEqual(list(Path(directory).iterdir()), [pdf])


if __name__ == "__main__":
    unittest.main()
