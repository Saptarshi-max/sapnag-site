"""
Batch convert all PNG/JPG/JPEG images to WebP format.
- Resizes images wider than MAX_WIDTH (1920px) while preserving aspect ratio
- Converts to WebP with quality 80 (good balance of size vs quality)
- Skips SVG, GIF, and already-WebP files
- Skips _site/, node_modules/, .venv/ directories
- Outputs a report of before/after sizes
- Updates all references in .md, .html, .yml, .yaml, .json, .css, .scss, .rb files
"""

import os
import re
import sys
from pathlib import Path
from PIL import Image

# --- Configuration ---
REPO_ROOT = Path(__file__).resolve().parent.parent
MAX_WIDTH = 1920
WEBP_QUALITY = 80
SKIP_DIRS = {'_site', 'node_modules', '.venv', '.git', 'scripts'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}
REF_FILE_EXTENSIONS = {'.md', '.html', '.yml', '.yaml', '.json', '.css', '.scss', '.rb', '.txt', '.xml'}

def should_skip(path: Path) -> bool:
    """Check if path is in a directory we should skip."""
    parts = path.relative_to(REPO_ROOT).parts
    return any(part in SKIP_DIRS for part in parts)

def convert_image(src: Path) -> tuple[Path, int, int] | None:
    """Convert a single image to WebP. Returns (dest_path, old_size, new_size) or None on failure."""
    try:
        img = Image.open(src)
    except Exception as e:
        print(f"  SKIP (can't open): {src} - {e}")
        return None

    # Handle RGBA for PNGs, convert palette/LA modes
    if img.mode in ('RGBA', 'LA'):
        pass  # WebP supports transparency
    elif img.mode == 'P':
        img = img.convert('RGBA')
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Resize if wider than MAX_WIDTH
    w, h = img.size
    if w > MAX_WIDTH:
        ratio = MAX_WIDTH / w
        new_h = int(h * ratio)
        img = img.resize((MAX_WIDTH, new_h), Image.LANCZOS)

    # Determine output path (same name, .webp extension)
    dest = src.with_suffix('.webp')

    old_size = src.stat().st_size

    # Save as WebP
    save_kwargs = {'quality': WEBP_QUALITY, 'method': 6}  # method 6 = slowest but best compression
    if img.mode in ('RGBA', 'LA'):
        save_kwargs['lossless'] = False  # lossy even for transparent
    img.save(dest, 'WEBP', **save_kwargs)

    new_size = dest.stat().st_size
    return dest, old_size, new_size

def find_all_images() -> list[Path]:
    """Find all convertible images in the repo."""
    images = []
    for root, dirs, files in os.walk(REPO_ROOT):
        root_path = Path(root)
        if should_skip(root_path):
            continue
        # Prune skipped directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            fp = root_path / f
            if fp.suffix.lower() in IMAGE_EXTENSIONS:
                images.append(fp)
    return sorted(images)

def find_ref_files() -> list[Path]:
    """Find all files that may contain image references."""
    ref_files = []
    for root, dirs, files in os.walk(REPO_ROOT):
        root_path = Path(root)
        if should_skip(root_path):
            continue
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            fp = root_path / f
            if fp.suffix.lower() in REF_FILE_EXTENSIONS:
                ref_files.append(fp)
    return sorted(ref_files)

def update_references(converted: dict[str, str]):
    """Update image references in all text files.
    
    converted: dict mapping old relative path (with original ext) -> new relative path (with .webp)
    """
    ref_files = find_ref_files()
    
    # Build a regex pattern that matches any of the old filenames
    # We need to handle both forward and backslash paths, and with/without leading /
    # Sort by length descending to match longer paths first
    old_paths = sorted(converted.keys(), key=len, reverse=True)
    
    if not old_paths:
        return 0
    
    total_replacements = 0
    
    for ref_file in ref_files:
        try:
            content = ref_file.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        
        original_content = content
        
        for old_rel in old_paths:
            new_rel = converted[old_rel]
            # Replace with forward slashes (web paths)
            old_web = old_rel.replace('\\', '/')
            new_web = new_rel.replace('\\', '/')
            if old_web in content:
                content = content.replace(old_web, new_web)
        
        if content != original_content:
            try:
                ref_file.write_text(content, encoding='utf-8')
                count = sum(1 for old_rel in old_paths if converted[old_rel].replace('\\', '/') in content)
                total_replacements += 1
                print(f"  Updated references in: {ref_file.relative_to(REPO_ROOT)}")
            except Exception as e:
                print(f"  ERROR updating {ref_file}: {e}")
    
    return total_replacements

def main():
    print(f"=== WebP Image Converter ===")
    print(f"Repo root: {REPO_ROOT}")
    print(f"Max width: {MAX_WIDTH}px | WebP quality: {WEBP_QUALITY}")
    print()
    
    # Phase 1: Find and convert images
    images = find_all_images()
    print(f"Found {len(images)} images to convert.\n")
    
    converted = {}  # old_relative_path -> new_relative_path
    total_old = 0
    total_new = 0
    failures = 0
    
    for img_path in images:
        rel = str(img_path.relative_to(REPO_ROOT))
        print(f"Converting: {rel}")
        
        result = convert_image(img_path)
        if result is None:
            failures += 1
            continue
        
        dest, old_size, new_size = result
        savings = (1 - new_size / old_size) * 100 if old_size > 0 else 0
        total_old += old_size
        total_new += new_size
        
        old_rel = str(img_path.relative_to(REPO_ROOT))
        new_rel = str(dest.relative_to(REPO_ROOT))
        converted[old_rel] = new_rel
        
        print(f"  {old_size/1024:.0f} KB -> {new_size/1024:.0f} KB ({savings:.1f}% smaller)")
    
    print(f"\n{'='*60}")
    print(f"CONVERSION COMPLETE")
    print(f"  Images converted: {len(converted)}")
    print(f"  Failures: {failures}")
    print(f"  Total before: {total_old/1024/1024:.2f} MB")
    print(f"  Total after:  {total_new/1024/1024:.2f} MB")
    print(f"  Total saved:  {(total_old-total_new)/1024/1024:.2f} MB ({(1-total_new/total_old)*100:.1f}%)")
    print()
    
    # Phase 2: Update references
    print("=== Updating file references ===")
    files_updated = update_references(converted)
    print(f"  Files updated: {files_updated}")
    print()
    
    # Phase 3: Delete old files
    print("=== Removing original image files ===")
    removed = 0
    for old_rel in converted:
        old_path = REPO_ROOT / old_rel
        if old_path.exists():
            old_path.unlink()
            removed += 1
    print(f"  Removed {removed} original files.")
    print()
    
    print("DONE! Remember to:")
    print("  1. Rebuild the Jekyll site to verify")
    print("  2. Check image-gallery.html if you use .jpg/.jpeg extensions in Liquid filters")

if __name__ == '__main__':
    main()
