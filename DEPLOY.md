# Deploying the Design Gallery (fast, no crazy load times)

You have **10,811 images = 4.7 GB**. That is far too heavy to dump onto a
normal static host. The trick is: **serve tiny WebP thumbnails, not the
4.7 GB of originals.** Do this and the gallery feels instant even on mobile data.

---

## Step 1 — Generate thumbnails (the single most important step)

```bash
python make_thumbs.py
```

This creates two new folders next to `extracted_images/`:

| Folder      | Size cap | Used for            | Typical size |
|-------------|----------|---------------------|--------------|
| `thumbs/`   | 500 px   | the gallery grids   | ~15–40 KB ea |
| `display/`  | 1400 px  | the full-screen viewer | ~120–200 KB ea |

The 4.7 GB of originals shrinks to roughly **300–500 MB of WebP**.
The site automatically uses `thumbs/` and `display/`, and falls back to the
original in `extracted_images/` only if a WebP is missing.

> Run it once. It skips files that already exist, so re-running after adding
> a new catalogue only processes the new images.

**After generating, you do NOT need to upload `extracted_images/` at all** —
only `thumbs/` and `display/`. (Keep the originals locally as your master copy.)

---

## Step 2 — Pick a host

### ✅ Recommended: Cloudflare Pages
- Free, global CDN (280+ cities) → low latency everywhere, including India.
- No bandwidth limits on the free plan.
- Caps: 20,000 files per deployment. With `thumbs/` + `display/` you have
  ~21,600 files — **just over the limit**, so do one of:
  - **Option A (simplest):** deploy only `thumbs/` + `display/` (~21.6k). If
    you trim a couple of duplicate catalogues in the admin you'll be under 20k.
  - **Option B (cleanest, scales forever):** put images on **Cloudflare R2**
    (object storage, zero egress fees) and deploy just the HTML to Pages.
    See Step 4.

### Alternatives
| Host | Good | Watch out |
|------|------|-----------|
| **Netlify** | drag-and-drop deploy | 100 GB/mo bandwidth on free; file count fine |
| **Vercel** | great DX | image-heavy static is fine, but 100 GB/mo soft cap |
| **GitHub Pages** | free, simple | 1 GB repo soft limit, 100 GB/mo — borderline |
| **Bunny.net CDN** | cheapest for pure image hosting, fast in Asia | paid (~\$0.01/GB) |

For your case, **Cloudflare Pages + R2** is the best long-term answer because
egress is free and it never hits a file-count wall.

---

## Step 3 — Deploy the simple way (Cloudflare Pages, no R2)

1. Generate thumbnails (Step 1).
2. Put these in one folder:
   ```
   index.html
   admin.html
   gallery.json
   thumbs/
   display/
   ```
3. Go to **dash.cloudflare.com → Workers & Pages → Create → Pages →
   Upload assets**, drag the folder in, deploy.
4. Done. You get a `*.pages.dev` URL (add a custom domain if you want).

If you stay under 20k files this is all you need.

---

## Step 4 — Scale path (Cloudflare R2 for the images)

Use this if you cross the file limit or keep adding catalogues.

1. Create an R2 bucket, enable its public URL (or put Cloudflare CDN in front).
2. Upload `thumbs/` and `display/` to the bucket (keep the same folder layout).
   ```bash
   # example with rclone or the Cloudflare dashboard / wrangler
   wrangler r2 object put <bucket>/thumbs ...   # or bulk upload via rclone
   ```
3. In `index.html`, point the image bases at the bucket:
   ```js
   const THUMB_BASE   = 'https://images.yourdomain.com/thumbs';
   const DISPLAY_BASE = 'https://images.yourdomain.com/display';
   const IMG_BASE     = 'https://images.yourdomain.com/extracted_images';
   ```
4. Deploy just `index.html`, `admin.html`, `gallery.json` to Pages.

Now the page loads in milliseconds and images stream from the CDN on demand.

---

## Why it'll be fast

- **WebP thumbnails** cut image weight ~90%.
- **Lazy loading** (`loading="lazy"`) — only images on screen download.
- **Two tiers** — the grid never loads a full-size image; the viewer only
  loads the medium 1400 px version, not the multi-MB original.
- **CDN edge caching** — repeat visits and nearby users are served locally.
- Cache headers are already set in `netlify.toml` (and Cloudflare caches
  static assets aggressively by default).

---

## Adding catalogues later

1. Open `admin.html`, select the new image folder, set name + category, **Add**.
2. **Export gallery.json** and replace the old one.
3. Copy the new folder into `extracted_images/`, run `python make_thumbs.py`.
4. Re-deploy (or upload the new `thumbs/`+`display/` subfolders + `gallery.json`).
