# JS 逆向完整流程说明

本文档描述本项目中「从签名生成到数据解码」的完整 JS 流程，并给出类封装结构，便于二次开发。

## 1. 流程总览

1. 清洗 API URL，去掉旧的 `msToken`、`a_bogus`。
2. 生成随机 `msToken`。
3. 本地加载 `webmssdk.js`，构造浏览器仿真沙箱。
4. 调用 `byted_acrawler.frontierSign(baseUrl)` 计算 `a_bogus`。
5. 携带 `msToken + a_bogus` 请求书库 API。
6. 提取 `book_list` 后，逐本访问 `/page/{book_id}`。
7. 解析 `window.__INITIAL_STATE__`，回填 `book_name/author/abstract/read_count/word_count`。
8. 输出摘要结果，按需落盘原始与解码 JSON。

## 2. 类封装

核心类：`FanqieReverseFlow`（文件：`fanqie_reverse_flow.js`）

主要方法：

- `normalizeBaseUrl(inputUrl)`：去除旧签名参数。
- `generateMsToken(length)`：生成 `msToken`。
- `ensureWebMsSdk()`：本地不存在 SDK 时自动下载。
- `generateABogus(baseUrl, msToken)`：在 VM 沙箱中计算 `a_bogus`。
- `requestSignedApi(inputUrl)`：发起签名请求并返回响应对象。
- `extractInitialStateObjectText(html)`：提取页面内初始状态对象文本。
- `parseInitialStateText(stateText)`：兼容解析对象文本。
- `fetchBookDetailState(bookId)`：抓取单本详情页状态。
- `decodeBookList(rawPayload)`：将混淆字段回填为可读内容。
- `runFullFlow(inputUrl, options)`：一键执行完整流程。

## 3. CLI 使用

入口文件：`fanqie_api_client.js`

### 仅请求并输出签名摘要

```bash
node fanqie_api_client.js "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index=0&gender=-1&category_id=-1&creation_status=-1&word_count=-1&book_type=-1&sort=0"
```

### 执行完整流程（含解码与文件输出）

```bash
node fanqie_api_client.js "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index=0&gender=-1&category_id=-1&creation_status=-1&word_count=-1&book_type=-1&sort=0" --decode --raw-out book_list_response.json --decoded-out book_list_decoded.json
```

## 4. 输出说明

- 命令行会输出摘要：`status`、`code`、`request_url`、`msToken`、`a_bogus` 等。
- 开启 `--decode` 时会额外输出：
  - `book_list_response.json`：原始接口返回。
  - `book_list_decoded.json`：详情页回填后的可读数据。

## 5. 合规提示

请仅在已授权目标上使用本流程，避免未授权抓取与调用。

