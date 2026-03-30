#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import pathlib
import time
from typing import Any, Dict, List, Tuple
from urllib.parse import urlencode

import execjs
import requests
import urllib3

import fanqie_execjs_client as core


def build_base_url(
    endpoint: str,
    page_index: int,
    page_count: int,
    gender: int,
    category_id: int,
    creation_status: int,
    word_count: int,
    book_type: int,
    sort: int,
) -> str:
    query = {
        "page_count": page_count,
        "page_index": page_index,
        "gender": gender,
        "category_id": category_id,
        "creation_status": creation_status,
        "word_count": word_count,
        "book_type": book_type,
        "sort": sort,
    }
    return f"{endpoint.rstrip('/')}?{urlencode(query)}"


def fetch_one_page(
    ctx: execjs.ExternalRuntime.Context,
    base_url: str,
    sdk_path: pathlib.Path,
    token_len: int,
    timeout: int,
    retry: int,
    insecure: bool,
) -> Tuple[Dict[str, Any], str]:
    headers = {
        "User-Agent": core.DEFAULT_UA,
        "Referer": core.DEFAULT_REFERER,
        "Accept": "application/json, text/plain, */*",
    }
    verify = not insecure

    last_err = ""
    for attempt in range(1, retry + 1):
        try:
            sign = ctx.call(
                "make_fanqie_params",
                base_url,
                str(sdk_path),
                core.DEFAULT_UA,
                core.DEFAULT_REFERER,
                token_len,
            )
            resp = requests.get(
                base_url,
                params={"msToken": sign["msToken"], "a_bogus": sign["a_bogus"]},
                headers=headers,
                timeout=timeout,
                verify=verify,
            )
            resp.raise_for_status()
            return resp.json(), resp.url
        except Exception as exc:
            last_err = f"attempt={attempt} error={exc}"
            if attempt < retry:
                time.sleep(0.6)
    raise RuntimeError(last_err)


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch crawl fanqie book_list by page index")
    parser.add_argument("--endpoint", default="https://fanqienovel.com/api/author/library/book_list/v0/")
    parser.add_argument("--page-start", type=int, default=0)
    parser.add_argument("--page-end", type=int, default=2, help="inclusive")
    parser.add_argument("--page-count", type=int, default=18)
    parser.add_argument("--gender", type=int, default=-1)
    parser.add_argument("--category-id", type=int, default=-1)
    parser.add_argument("--creation-status", type=int, default=-1)
    parser.add_argument("--word-count", type=int, default=-1)
    parser.add_argument("--book-type", type=int, default=-1)
    parser.add_argument("--sort", type=int, default=0)
    parser.add_argument("--token-len", type=int, default=132)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--retry", type=int, default=3)
    parser.add_argument("--sleep", type=float, default=0.2, help="seconds between pages")
    parser.add_argument("--insecure", action="store_true")
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument("--sdk-path", default="webmssdk.js")
    parser.add_argument("--out-dir", default="batch_output")
    args = parser.parse_args()

    if args.page_end < args.page_start:
        raise ValueError("--page-end must be >= --page-start")

    if args.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    out_dir = pathlib.Path(args.out_dir).resolve()
    raw_dir = out_dir / "raw_pages"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    sdk_path = pathlib.Path(args.sdk_path).resolve()
    core.ensure_sdk(sdk_path)
    ctx = execjs.compile(core.JS_BRIDGE)

    all_books: List[Dict[str, Any]] = []
    page_reports: List[Dict[str, Any]] = []

    for page_index in range(args.page_start, args.page_end + 1):
        base_url = build_base_url(
            endpoint=args.endpoint,
            page_index=page_index,
            page_count=args.page_count,
            gender=args.gender,
            category_id=args.category_id,
            creation_status=args.creation_status,
            word_count=args.word_count,
            book_type=args.book_type,
            sort=args.sort,
        )
        print(f"[page {page_index}] requesting ...")
        try:
            data, req_url = fetch_one_page(
                ctx=ctx,
                base_url=base_url,
                sdk_path=sdk_path,
                token_len=args.token_len,
                timeout=args.timeout,
                retry=args.retry,
                insecure=args.insecure,
            )
            page_file = raw_dir / f"page_{page_index}.json"
            page_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

            books = ((data.get("data") or {}).get("book_list") or [])
            for b in books:
                item = dict(b)
                item["__page_index"] = page_index
                all_books.append(item)

            report = {
                "page_index": page_index,
                "ok": True,
                "request_url": req_url,
                "code": data.get("code"),
                "book_count": len(books),
                "saved_raw": str(page_file),
            }
            page_reports.append(report)
            print(f"[page {page_index}] ok, books={len(books)}")
        except Exception as exc:
            report = {
                "page_index": page_index,
                "ok": False,
                "error": str(exc),
            }
            page_reports.append(report)
            print(f"[page {page_index}] failed: {exc}")
            if args.stop_on_error:
                break

        if args.sleep > 0:
            time.sleep(args.sleep)

    merged_path = out_dir / "merged_book_list.json"
    merged_path.write_text(json.dumps(all_books, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "endpoint": args.endpoint,
        "page_start": args.page_start,
        "page_end": args.page_end,
        "page_count_param": args.page_count,
        "total_books": len(all_books),
        "success_pages": sum(1 for x in page_reports if x.get("ok")),
        "failed_pages": sum(1 for x in page_reports if not x.get("ok")),
        "merged_file": str(merged_path),
        "pages": page_reports,
    }
    summary_path = out_dir / "crawl_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("done")
    print(f"summary: {summary_path}")
    print(f"merged : {merged_path}")
    print(f"total_books: {len(all_books)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

