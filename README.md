# tomato_Novel

这是一个用于番茄小说接口请求与数据解码的工具仓库。

## 功能简介

1. 在本地生成接口请求参数（如 `msToken`、`a_bogus`）。
2. 请求书库接口并获取原始返回数据。
3. 通过详情页回填，修复 `book_list` 中的混淆字段。

## 快速使用

### Node.js 请求示例

```bash
node fanqie_api_client.js "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index=0&gender=-1&category_id=-1&creation_status=-1&word_count=-1&book_type=-1&sort=0"
```

### Python + ExecJS 请求示例

```bash
python fanqie_execjs_client.py --insecure "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index=0&gender=-1&category_id=-1&creation_status=-1&word_count=-1&book_type=-1&sort=0"
```

### 按页批量抓取

```bash
python batch_crawl_by_page.py --page-start 0 --page-end 9 --page-count 18 --insecure --out-dir runs/page_0_9
```

## 说明

- 详细技术说明请查看 `TECHNICAL_DOC.md`。
- 请仅在你已授权的目标上使用本工具。
