#!/usr/bin/env python3
"""
make_thumbs.py — Generate fast-loading WebP versions of all designs.

Creates two tiers that mirror the extracted_images/ folder structure:
  thumbs/   → max 500px,  WebP q72  (used in the gallery grids)
  display/  → max 1400px, WebP q82  (used in the full-screen photo viewer)

Originals in extracted_images/ are never modified.

Run:  python make_thumbs.py
"""
import os, sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from PIL import Image, ImageOps

ROOT     = os.path.dirname(os.path.abspath(__file__))
SRC      = os.path.join(ROOT, "extracted_images")
THUMB    = os.path.join(ROOT, "thumbs")
DISPLAY  = os.path.join(ROOT, "display")

THUMB_MAX   = 500
DISPLAY_MAX = 1400
THUMB_Q     = 72
DISPLAY_Q   = 82

VALID = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


def process(args):
    src_path, rel = args
    out_thumb   = os.path.join(THUMB,   rel)
    out_display = os.path.join(DISPLAY, rel)
    out_thumb   = os.path.splitext(out_thumb)[0]   + ".webp"
    out_display = os.path.splitext(out_display)[0]  + ".webp"

    # Skip if both already exist
    if os.path.exists(out_thumb) and os.path.exists(out_display):
        return 0

    try:
        os.makedirs(os.path.dirname(out_thumb), exist_ok=True)
        os.makedirs(os.path.dirname(out_display), exist_ok=True)

        with Image.open(src_path) as im:
            im = ImageOps.exif_transpose(im)
            if im.mode in ("RGBA", "P", "LA"):
                im = im.convert("RGB")

            # display tier
            if not os.path.exists(out_display):
                d = im.copy()
                d.thumbnail((DISPLAY_MAX, DISPLAY_MAX), Image.LANCZOS)
                d.save(out_display, "WEBP", quality=DISPLAY_Q, method=4)

            # thumb tier
            if not os.path.exists(out_thumb):
                t = im.copy()
                t.thumbnail((THUMB_MAX, THUMB_MAX), Image.LANCZOS)
                t.save(out_thumb, "WEBP", quality=THUMB_Q, method=4)
        return 1
    except Exception as e:
        print(f"  ! {rel}: {e}")
        return 0


def collect():
    jobs = []
    for dirpath, _, files in os.walk(SRC):
        for f in files:
            if f.lower().endswith(VALID):
                full = os.path.join(dirpath, f)
                rel  = os.path.relpath(full, SRC)
                jobs.append((full, rel))
    return jobs


def main():
    if not os.path.isdir(SRC):
        print(f"Source folder not found: {SRC}")
        sys.exit(1)

    jobs = collect()
    total = len(jobs)
    print(f"Found {total} images. Generating WebP thumbnails…\n")

    done = 0
    with ProcessPoolExecutor() as ex:
        futures = [ex.submit(process, j) for j in jobs]
        for i, fut in enumerate(as_completed(futures), 1):
            done += fut.result()
            if i % 200 == 0 or i == total:
                pct = i * 100 // total
                print(f"  [{pct:3d}%] processed {i}/{total}")

    print(f"\nDone. New files generated: {done}")
    print(f"thumbs/   → {THUMB}")
    print(f"display/  → {DISPLAY}")


if __name__ == "__main__":
    main()
