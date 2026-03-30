const fs = require("fs");
const path = require("path");

const INPUT_FILE = path.resolve(process.argv[2] || "book_list_response.json");
const OUTPUT_FILE = path.resolve(process.argv[3] || "book_list_decoded.json");
const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

function extractInitialStateObjectText(html) {
  const marker = "window.__INITIAL_STATE__=";
  const idx = html.indexOf(marker);
  if (idx < 0) return null;

  let i = idx + marker.length;
  while (i < html.length && html[i] !== "{") i += 1;
  if (i >= html.length) return null;

  let depth = 0;
  let inString = false;
  let quote = "";
  let escaped = false;
  const start = i;

  for (; i < html.length; i += 1) {
    const ch = html[i];
    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (ch === "\\") {
        escaped = true;
      } else if (ch === quote) {
        inString = false;
        quote = "";
      }
      continue;
    }

    if (ch === '"' || ch === "'") {
      inString = true;
      quote = ch;
      continue;
    }

    if (ch === "{") {
      depth += 1;
      continue;
    }
    if (ch === "}") {
      depth -= 1;
      if (depth === 0) {
        return html.slice(start, i + 1);
      }
    }
  }

  return null;
}

async function fetchPageState(bookId) {
  const url = `https://fanqienovel.com/page/${bookId}`;
  const res = await fetch(url, { headers: { "user-agent": UA } });
  if (!res.ok) {
    throw new Error(`fetch page failed: ${bookId} ${res.status}`);
  }
  const html = await res.text();
  const stateText = extractInitialStateObjectText(html);
  if (!stateText) {
    throw new Error(`initial state not found: ${bookId}`);
  }
  const state = JSON.parse(stateText);
  return state.page || {};
}

function normalizeCountText(num) {
  if (typeof num !== "number" || !Number.isFinite(num)) return null;
  if (num >= 100000000) return `${(num / 100000000).toFixed(1)}亿`;
  if (num >= 10000) return `${(num / 10000).toFixed(1)}万`;
  return String(num);
}

async function main() {
  const raw = JSON.parse(fs.readFileSync(INPUT_FILE, "utf8"));
  const list = ((raw || {}).data || {}).book_list || [];
  const outList = [];

  for (let i = 0; i < list.length; i += 1) {
    const item = { ...list[i] };
    const bookId = item.book_id;
    process.stdout.write(`[${i + 1}/${list.length}] ${bookId} ... `);

    try {
      const page = await fetchPageState(bookId);
      if (page.bookName) item.book_name = page.bookName;
      if (page.author) item.author = page.author;
      if (page.abstract) item.abstract = page.abstract;
      if (typeof page.readCount === "number") {
        item.read_count = normalizeCountText(page.readCount) || String(page.readCount);
      }
      if (typeof page.wordNumber === "number") {
        item.word_count = normalizeCountText(page.wordNumber) || String(page.wordNumber);
      }
      process.stdout.write("ok\n");
    } catch (err) {
      process.stdout.write(`skip (${err.message})\n`);
    }

    outList.push(item);
  }

  const out = {
    ...raw,
    data: {
      ...(raw.data || {}),
      book_list: outList,
    },
  };
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(out, null, 2), "utf8");
  console.log(`saved => ${OUTPUT_FILE}`);
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
});

