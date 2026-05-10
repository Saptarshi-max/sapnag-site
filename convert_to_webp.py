"""Convert remaining PNG/JPG images to WebP and resize if oversized."""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
MAX_WIDTH = 1920
WEBP_QUALITY = 82
SKIP_DIRS = {"_site", "node_modules", ".git", "bower_components", ".venv"}
CONVERTIBLE = {".png", ".jpg", ".jpeg"}
# Don't convert icons/favicons
SKIP_FILES = {"favicon.ico", "favicon12.ico", "favicon_big.ico"}

converted = []
skipped = []

for dirpath, dirnames, filenames in os.walk(ROOT):
    # Prune skipped directories
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    
    for fname in filenames:
        ext = os.path.splitext(fname)[1].lower()
        if ext not in CONVERTIBLE:
            continue
        if fname in SKIP_FILES:
            continue
            
        src = os.path.join(dirpath, fname)
        webp_name = os.path.splitext(fname)[0] + ".webp"
        dst = os.path.join(dirpath, webp_name)
        
        # Skip if webp already exists
        if os.path.exists(dst):
            skipped.append((src, "webp already exists"))
            continue
        
        try:
            img = Image.open(src)
            # Convert RGBA PNGs properly
            if img.mode in ("RGBA", "LA"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            
            orig_size = img.size
            # Resize if wider than MAX_WIDTH
            if img.width > MAX_WIDTH:
                ratio = MAX_WIDTH / img.width
                new_height = int(img.height * ratio)
                img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)
            
            img.save(dst, "WEBP", quality=WEBP_QUALITY)
            
            src_size = os.path.getsize(src) / 1024
            dst_size = os.path.getsize(dst) / 1024
            savings = ((src_size - dst_size) / src_size) * 100 if src_size > 0 else 0
            
            resized = f" (resized {orig_size[0]}x{orig_size[1]} → {img.width}x{img.height})" if img.width != orig_size[0] else ""
            rel = os.path.relpath(src, ROOT)
            print(f"✓ {rel}: {src_size:.0f}K → {dst_size:.0f}K ({savings:.0f}% smaller){resized}")
            converted.append(rel)
            
        except Exception as e:
            print(f"✗ {os.path.relpath(src, ROOT)}: {e}")
            skipped.append((src, str(e)))

print(f"\n--- Converted {len(converted)} images ---")
if skipped:
    print(f"--- Skipped {len(skipped)} (already have .webp) ---")
    for s, reason in skipped:
        print(f"  {os.path.relpath(s, ROOT)}: {reason}")
