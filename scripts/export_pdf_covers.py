import os
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF (pymupdf) is not installed. Please install it before running.")
    sys.exit(1)


def find_pdfs(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        for name in filenames:
            if name.lower().endswith(".pdf"):
                yield Path(dirpath) / name


def export_first_page_to_png(pdf_path: Path, out_root: Path, root: Path, scale: float = 2.0):
    rel_dir = pdf_path.parent.relative_to(root)
    out_dir = out_root / rel_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / (pdf_path.stem + ".png")

    with fitz.open(pdf_path) as doc:
        if doc.page_count == 0:
            print(f"[skip] No pages: {pdf_path}")
            return False
        page = doc.load_page(0)
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        pix.save(out_path)

    print(f"[ok] {pdf_path} -> {out_path}")
    return True


def main():
    root = Path(__file__).resolve().parents[1]  # workspace root
    out_root = root / "pdf_covers"
    out_root.mkdir(exist_ok=True)

    pdfs = list(find_pdfs(root))
    if not pdfs:
        print("No PDF files found.")
        return

    print(f"Found {len(pdfs)} PDF(s). Converting first page to PNG...")
    converted = 0
    for pdf in pdfs:
        try:
            if export_first_page_to_png(pdf, out_root, root):
                converted += 1
        except Exception as e:
            print(f"[error] {pdf}: {e}")

    print(f"Done. Converted {converted}/{len(pdfs)} PDF(s).")
    print(f"Output folder: {out_root}")


if __name__ == "__main__":
    main()
