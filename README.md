# tomato_Novel

Fanqie API param generation + request + book list decode toolkit.

## Quick Start

### Python deps

```bash
python -m pip install -r requirements.txt
```

### Node request

```bash
node fanqie_api_client.js "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index=0&gender=-1&category_id=-1&creation_status=-1&word_count=-1&book_type=-1&sort=0"
```

### Python + ExecJS request

```bash
python fanqie_execjs_client.py --insecure "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index=0&gender=-1&category_id=-1&creation_status=-1&word_count=-1&book_type=-1&sort=0"
```

### Batch crawl by page index

```bash
python batch_crawl_by_page.py --page-start 0 --page-end 9 --page-count 18 --insecure --out-dir runs/page_0_9
```

### Decode obfuscated book_list text

```bash
node decode_book_list_from_pages.js book_list_response.json book_list_decoded.json
```

Detailed notes: `TECHNICAL_DOC.md`
