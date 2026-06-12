const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { readFileSync } = require('fs');
const { join, relative } = require('path');
const { readdir } = require('fs/promises');

const ACCOUNT_ID = '1aa1e67231e0c1a629e1f9b25fa945ef';
const BUCKET = 'amma-design-gallery';
const ENDPOINT = `https://${ACCOUNT_ID}.r2.cloudflarestorage.com`;

const ACCESS_KEY = process.env.R2_ACCESS_KEY_ID;
const SECRET_KEY = process.env.R2_SECRET_ACCESS_KEY;

if (!ACCESS_KEY || !SECRET_KEY) {
  console.error('Set R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY environment variables');
  process.exit(1);
}

const s3 = new S3Client({
  region: 'auto',
  endpoint: ENDPOINT,
  credentials: { accessKeyId: ACCESS_KEY, secretAccessKey: SECRET_KEY },
  forcePathStyle: true,
});

const MIME = { '.webp': 'image/webp', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif', '.svg': 'image/svg+xml' };

let total = 0, uploaded = 0, failed = 0, queued = 0;
const start = Date.now();
const CONCURRENCY = 20;

async function uploadFile(filePath, key) {
  const ext = filePath.slice(filePath.lastIndexOf('.')).toLowerCase();
  const contentType = MIME[ext] || 'application/octet-stream';
  const cmd = new PutObjectCommand({
    Bucket: BUCKET,
    Key: key,
    Body: readFileSync(filePath),
    ContentType: contentType,
    CacheControl: 'public, max-age=31536000, immutable',
  });
  await s3.send(cmd);
}

async function collectFiles(dir, base, list) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = join(dir, e.name);
    if (e.isDirectory()) {
      await collectFiles(full, base, list);
    } else if (e.name.endsWith('.webp')) {
      total++;
      list.push({ path: full, key: relative(base, full).replace(/\\/g, '/') });
    }
  }
}

async function run() {
  const root = process.cwd();
  const files = [];

  console.log('Scanning files...');
  await collectFiles(join(root, 'thumbs'), root, files);
  await collectFiles(join(root, 'display'), root, files);
  console.log(`Found ${files.length} files. Uploading with ${CONCURRENCY} workers...\n`);

  let idx = 0;
  const workers = [];

  async function worker(id) {
    while (idx < files.length) {
      const i = idx++;
      const { path, key } = files[i];
      try {
        await uploadFile(path, key);
        uploaded++;
      } catch (err) {
        failed++;
        console.error(`\n  [w${id}] FAIL: ${key} — ${err.message}`);
      }
      if (uploaded % 200 === 0 || uploaded === files.length) {
        const pct = ((uploaded / files.length) * 100).toFixed(1);
        const elapsed = ((Date.now() - start) / 1000).toFixed(0);
        const rate = (uploaded / elapsed).toFixed(0);
        process.stdout.write(`\r  ${pct}% | ${uploaded}/${files.length} | ${elapsed}s | ${rate}/s | failed: ${failed}`);
      }
    }
  }

  for (let w = 0; w < CONCURRENCY; w++) {
    workers.push(worker(w));
  }
  await Promise.all(workers);

  const elapsed = ((Date.now() - start) / 1000).toFixed(0);
  console.log(`\n\nDone in ${elapsed}s — ${uploaded} uploaded, ${failed} failed, ${files.length} total`);
}

run().catch(err => { console.error(err); process.exit(1); });
