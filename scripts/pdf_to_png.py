"""Render PDF pages to PNG. No OCR or text extraction. Python 3.10+."""

import argparse
from datetime import datetime
from getpass import getpass
import math
from pathlib import Path
import re
import sys
import tempfile
import time


def clean_path(value):
    """Accept Windows 'Copy as path' values, including surrounding quotes."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    if not value:
        raise ValueError("路徑不能空白。")
    return Path(value).expanduser().resolve()


def select_pages(spec, total):
    spec = spec.strip().lower()
    if spec in ("all", "全部"):
        return list(range(total))
    selected = set()
    for token in spec.split(","):
        match = re.fullmatch(r"\s*([0-9]+)(?:\s*-\s*([0-9]+))?\s*", token)
        if not match:
            raise ValueError("頁碼格式請用 7、1,3,7、2-5 或 all。")
        start = int(match[1])
        end = int(match[2] or match[1])
        if not 1 <= start <= end <= total:
            raise ValueError(f"頁碼必須介於 1 到 {total}，範圍也必須由小到大。")
        selected.update(range(start - 1, end))
    return sorted(selected)


def main():
    parser = argparse.ArgumentParser(description="把 PDF 頁面渲染成 PNG（不使用 OCR）。")
    parser.add_argument("pdf", nargs="?", help="PDF 路徑；省略則互動輸入")
    parser.add_argument("-p", "--pages", help="7、1,3,7、2-5 或 all；指令模式預設 all")
    parser.add_argument("-o", "--output", help="輸出根目錄；每次會建立新的子資料夾")
    parser.add_argument("--dpi", type=int, help="解析度，36 至 600，預設 200")
    args = parser.parse_args()

    try:
        import pymupdf
    except ImportError:
        print("缺少 PyMuPDF。請先執行：python -m pip install -r requirements.txt", file=sys.stderr)
        return 1

    interactive = args.pdf is None
    run_dir = None
    completed = 0
    try:
        pdf = clean_path(input("PDF 路徑（可以貼上含引號的路徑）：") if interactive else args.pdf)
        if not pdf.is_file():
            raise ValueError(f"找不到 PDF 檔案：{pdf}")
        with pymupdf.open(pdf) as doc:
            if not doc.is_pdf:
                raise ValueError("輸入檔案不是 PDF。")
            if doc.needs_pass:
                if not sys.stdin.isatty():
                    raise ValueError("PDF 需要密碼，請在終端機直接執行工具後輸入密碼。")
                if not doc.authenticate(getpass("PDF 密碼（輸入時不顯示）：")):
                    raise ValueError("PDF 密碼不正確。")
            if doc.page_count == 0:
                raise ValueError("PDF 沒有可轉換的頁面。")
            print(f"PDF 共 {doc.page_count} 頁；頁碼從 1 開始，依 PDF 頁面順序計算。")
            spec = args.pages
            if spec is None:
                spec = (input("頁碼（例：7、1,3,7、2-5、all；Enter = 全部）：").strip() or "all") if interactive else "all"
            pages = select_pages(spec, doc.page_count)
            dpi = args.dpi
            if dpi is None:
                dpi = int(input("DPI（Enter = 200）：").strip() or "200") if interactive else 200
            if not 36 <= dpi <= 600:
                raise ValueError("DPI 請使用 36 到 600 之間的整數。")
            output = args.output
            if interactive and output is None:
                output = input("輸出根目錄（Enter = PDF 旁的「檔名_png」資料夾）：").strip() or None
            root = clean_path(output) if output else pdf.parent / (pdf.stem + "_png")
            # Preflight pixel count to avoid unexpectedly large raster allocations.
            for index in pages:
                rect = doc[index].rect
                pixels = math.ceil(rect.width * dpi / 72) * math.ceil(rect.height * dpi / 72)
                if pixels > 50_000_000:
                    raise ValueError(f"第 {index + 1} 頁超過 5,000 萬像素，請降低 DPI。")
            root.mkdir(parents=True, exist_ok=True)
            # Unique directory prevents overwriting earlier conversions.
            run_dir = Path(tempfile.mkdtemp(prefix=datetime.now().strftime("run_%Y%m%d_%H%M%S_"), dir=root))
            print(f"輸出位置：{run_dir}")
            started = time.perf_counter()
            width = max(3, len(str(doc.page_count)))
            for index in pages:
                target = run_dir / f"page_{index + 1:0{width}d}.png"
                page_started = time.perf_counter()
                pix = doc[index].get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False, annots=True)
                # Encode before opening the file so interrupted rendering leaves no PNG.
                data = pix.tobytes("png")
                size = (pix.width, pix.height)
                del pix
                try:
                    with target.open("xb") as stream:
                        stream.write(data)
                except BaseException:
                    target.unlink(missing_ok=True)
                    raise
                del data
                completed += 1
                print(f"[{completed}/{len(pages)}] {target.name}  {size[0]}×{size[1]}  {time.perf_counter() - page_started:.2f} 秒")
            print(f"完成：{completed} 頁，共 {time.perf_counter() - started:.2f} 秒。\n圖片位於：{run_dir}")
        return 0
    except (KeyboardInterrupt, EOFError):
        print("\n已取消。", file=sys.stderr)
        code = 130
    except MemoryError:
        print("記憶體不足，請降低 DPI 或一次只轉一頁。", file=sys.stderr)
        code = 1
    except Exception as exc:
        print(f"轉換失敗：{exc}", file=sys.stderr)
        code = 1
    if run_dir is not None:
        print(f"本次已完成 {completed} 頁；請檢查：{run_dir}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
