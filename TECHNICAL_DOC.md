# tomato_Novel 技术说明

## 项目概览

本仓库主要用于：

1. 本地生成请求签名相关参数。
2. 请求番茄小说书库接口。
3. 将混淆文本字段回填为可读中文内容。

## 主要文件

- `fanqie_api_client.js`：Node.js 请求客户端。
- `fanqie_execjs_client.py`：Python + ExecJS 请求客户端。
- `decode_book_list_from_pages.js`：详情页回填与解码脚本。
- `batch_crawl_by_page.py`：按页批量抓取与汇总脚本。
- `inspect_page.js`：页面调试辅助脚本。

## 运行环境

- Node.js >= 18
- Python >= 3.9

## 依赖安装

```bash
python -m pip install -r requirements.txt
```

Python 第三方库：

- `PyExecJS`
- `requests`
- `urllib3`

## 常用命令

### Node.js 请求

```bash
node fanqie_api_client.js "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index=0&gender=-1&category_id=-1&creation_status=-1&word_count=-1&book_type=-1&sort=0"
```

### Python + ExecJS 请求

```bash
python fanqie_execjs_client.py --insecure "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index=0&gender=-1&category_id=-1&creation_status=-1&word_count=-1&book_type=-1&sort=0"
```

### 按页抓取

```bash
python batch_crawl_by_page.py --page-start 0 --page-end 9 --page-count 18 --insecure --out-dir runs/page_0_9
```

## 注意事项

- 返回数据可能存在私有区字符混淆，需通过详情页回填修复。
- 仅建议用于已获得授权的测试或研究场景。
