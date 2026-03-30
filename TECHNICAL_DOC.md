# tomato_Novel Fanqie API Toolkit

## Overview

This repo contains a practical toolkit to:

1. Generate `msToken` and `a_bogus` locally.
2. Call Fanqie API endpoints (example: `author/library/book_list`).
3. Decode obfuscated `book_list` fields by refilling from book detail pages.

---

## Files

- `fanqie_api_client.js`
  - Pure Node.js client.
  - Loads `webmssdk.js` in a VM sandbox and generates `a_bogus`.

- `fanqie_execjs_client.py`
  - Python + ExecJS client.
  - Uses JS bridge to generate sign params, then requests API with `requests`.

- `decode_book_list_from_pages.js`
  - Reads API result and rewrites readable fields from detail pages.

- `batch_crawl_by_page.py`
  - Batch crawler by `page_index` range.
  - Saves per-page raw JSON and merged list with `__page_index`.

- `inspect_page.js`
  - Quick page debug utility.

- `book_list_decoded.json`
  - Sample decoded output dataset.

- `requirements.txt`
  - Python dependencies.

- `requirment.txt`
  - Compatibility alias for users who type this filename.

---

## Environment

- Node.js `>= 18`
- Python `>= 3.9`

---

## Install

```bash
python -m pip install -r requirements.txt
```

or:

```bash
python -m pip install -r requirment.txt
```

---

## Usage

### 1) Node client

```bash
node fanqie_api_client.js "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index=0&gender=-1&category_id=-1&creation_status=-1&word_count=-1&book_type=-1&sort=0"
```

### 2) Python + ExecJS client

```bash
python fanqie_execjs_client.py --insecure "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index=0&gender=-1&category_id=-1&creation_status=-1&word_count=-1&book_type=-1&sort=0"
```

`--insecure` is for local SSL-chain issues only.

### 3) Decode book list text

```bash
node decode_book_list_from_pages.js book_list_response.json book_list_decoded.json
```

### 4) Batch crawl by page index

```bash
python batch_crawl_by_page.py --page-start 0 --page-end 9 --page-count 18 --insecure --out-dir runs/page_0_9
```

Output files:

- `runs/page_0_9/raw_pages/page_{index}.json`
- `runs/page_0_9/merged_book_list.json`
- `runs/page_0_9/crawl_summary.json`

---

## Notes

- `book_list` fields may contain private-use Unicode obfuscation.
- The decoder script fixes this by pulling canonical values from `/page/{book_id}`.
- Use only on authorized targets.
