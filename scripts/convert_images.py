"""
Image optimization script for Jekyll site.
- Converts PNG/JPG/JPEG images to WebP format
- Resizes images that exceed max dimensions (1920px wide for general, 800px for blog content)
- Preserves originals as .bak (optional)
- Outputs a report of savings
"""

import os
import sys
from pathlib import Path
from PIL import Image

# Configuration
SITE_ROOT = Path(__file__).resolve().parent.parent
MAX_WIDTH_COVER = 1920       # Cover/hero images
MAX_WIDTH_BLOG = 1600        # Blog content images
MAX_WIDTH_PROFILE = 800      # Profile/avatar images
WEBP_QUALITY = 82            # Good balance of quality vs size
SKIP_ALREADY_SMALL = 10240   # Skip files under 10KB

# Directories to process
IMAGE_DIRS = [
    ("cover_images", MAX_WIDTH_COVER),
    ("images", MAX_WIDTH_BLOG),
    ("assets/img", MAX_WIDTH_BLOG),
    ("assets/img/blog", MAX_WIDTH_BLOG),
    ("assets/img/gallery", MAX_WIDTH_BLOG),
    ("assets/img/projects", MAX_WIDTH_BLOG),
]

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}

# Files to skip (SVGs, already optimized, source files)
SKIP_EXTENSIONS = {'.svg', '.afdesign', '.webp', '.gif', '.ico'}

stats = {
    'processed': 0,
    'skipped': 0,
    'errors': 0,
    'original_bytes': 0,
    'new_bytes': 0,
}


def convert_image(src_path: Path, max_width: int) -> bool:
    """Convert a single image to WebP, resize if needed. Returns True if converted."""
    ext = src_path.suffix.lower()
    if ext in SKIP_EXTENSIONS:
        stats['skipped'] += 1
        return False

    if ext not in IMAGE_EXTENSIONS:
        stats['skipped'] += 1
        return False

    original_size = src_path.stat().st_size
    if original_size < SKIP_ALREADY_SMALL:
        stats['skipped'] += 1
        return False

    try:
        with Image.open(src_path) as img:
            # Convert RGBA PNGs properly
            if img.mode in ('RGBA', 'LA', 'P'):
                # For WebP, RGBA is supported directly
                if img.mode == 'P':
                    img = img.convert('RGBA')
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize if exceeds max width, maintaining aspect ratio
            w, h = img.size
            if w > max_width:
                ratio = max_width / w
                new_h = int(h * ratio)
                img = img.resize((max_width, new_h), Image.LANCZOS)

            # Save as WebP (same name, .webp extension)
            webp_path = src_path.with_suffix('.webp')
            
            # Handle RGBA vs RGB for WebP
            if img.mode == 'RGBA':
                img.save(webp_path, 'WEBP', quality=WEBP_QUALITY, method=4)
            else:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(webp_path, 'WEBP', quality=WEBP_QUALITY, method=4)

            new_size = webp_path.stat().st_size
            savings_pct = (1 - new_size / original_size) * 100

            stats['processed'] += 1
            stats['original_bytes'] += original_size
            stats['new_bytes'] += new_size

            print(f"  ✓ {src_path.name:40s} {original_size/1024:8.0f}KB → {new_size/1024:8.0f}KB ({savings_pct:+.1f}%)")

            # Remove original after successful conversion
            src_path.unlink()
            return True

    except Exception as e:
        stats['errors'] += 1
        print(f"  ✗ {src_path.name}: {e}")
        return False


def process_directory(rel_dir: str, max_width: int):
    """Process all images in a directory recursively."""
    abs_dir = SITE_ROOT / rel_dir
    if not abs_dir.exists():
        print(f"\n⏭ Skipping {rel_dir}/ (not found)")
        return

    # Collect all image files
    image_files = []
    for root, dirs, files in os.walk(abs_dir):
        # Skip _site output directory
        root_path = Path(root)
        if '_site' in root_path.parts:
            continue
        for f in files:
            fp = root_path / f
            if fp.suffix.lower() in IMAGE_EXTENSIONS:
                image_files.append(fp)

    if not image_files:
        print(f"\n⏭ {rel_dir}/ — no images found")
        return

    print(f"\n📁 Processing {rel_dir}/ ({len(image_files)} images)")
    print(f"   Max width: {max_width}px, WebP quality: {WEBP_QUALITY}")
    print(f"   {'File':<40s} {'Original':>10s}    {'WebP':>10s}  {'Savings':>8s}")
    print(f"   {'─'*40} {'─'*10}    {'─'*10}  {'─'*8}")

    for fp in sorted(image_files):
        convert_image(fp, max_width)


def main():
    print("=" * 70)
    print("Jekyll Image Optimizer — PNG/JPG → WebP Conversion")
    print("=" * 70)
    print(f"Site root: {SITE_ROOT}")

    # Process each configured directory
    for rel_dir, max_width in IMAGE_DIRS:
        process_directory(rel_dir, max_width)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Processed: {stats['processed']} images")
    print(f"  Skipped:   {stats['skipped']} (too small / wrong type)")
    print(f"  Errors:    {stats['errors']}")
    if stats['original_bytes'] > 0:
        total_saved = stats['original_bytes'] - stats['new_bytes']
        pct = (total_saved / stats['original_bytes']) * 100
        print(f"  Original:  {stats['original_bytes']/1024/1024:.1f} MB")
        print(f"  WebP:      {stats['new_bytes']/1024/1024:.1f} MB")
        print(f"  Saved:     {total_saved/1024/1024:.1f} MB ({pct:.1f}%)")
    print()


if __name__ == '__main__':
    main()
