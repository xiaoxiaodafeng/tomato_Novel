#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import pathlib
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import execjs
import requests
import urllib3

DEFAULT_SDK_URL = "https://lf3-cdn-tos.bytescm.com/obj/rc-web-sdk/webmssdk.js"
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_REFERER = "https://fanqienovel.com/"

JS_BRIDGE = r"""
const fs = require("fs");
const vm = require("vm");

function randomFromCharset(length, charset) {
  let out = "";
  for (let i = 0; i < length; i += 1) {
    const idx = Math.floor(Math.random() * charset.length);
    out += charset[idx];
  }
  return out;
}

function generateMsToken(length) {
  const charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
  return randomFromCharset(length, charset) + "==";
}

function createSandbox(userAgent, referer, msToken) {
  const noop = function(){};
  const immediateTimeout = function(fn) {
    try { if (typeof fn === "function") fn(); } catch (e) {}
    return 0;
  };
  const sandbox = {
    console: console,
    Buffer: Buffer,
    URL: URL,
    URLSearchParams: URLSearchParams,
    TextEncoder: TextEncoder,
    TextDecoder: TextDecoder,
    crypto: globalThis.crypto,
    fetch: globalThis.fetch,
    Request: globalThis.Request,
    Response: globalThis.Response,
    Headers: globalThis.Headers,
    atob: globalThis.atob,
    btoa: globalThis.btoa,
    setTimeout: immediateTimeout,
    clearTimeout: noop,
    setInterval: function(){ return 0; },
    clearInterval: noop,
    XMLHttpRequest: function XMLHttpRequest(){},
    location: {
      href: "https://fanqienovel.com/",
      origin: "https://fanqienovel.com",
      hostname: "fanqienovel.com",
      protocol: "https:",
      host: "fanqienovel.com",
      pathname: "/",
    },
    navigator: {
      userAgent: userAgent,
      platform: "Win32",
      language: "zh-CN",
      languages: ["zh-CN", "zh"],
      hardwareConcurrency: 8,
      deviceMemory: 8,
    },
    screen: {
      width: 1920,
      height: 1080,
      availWidth: 1920,
      availHeight: 1040,
      colorDepth: 24,
      pixelDepth: 24,
    },
    document: {
      referrer: referer,
      cookie: "xmst=" + msToken,
      hidden: false,
      visibilityState: "visible",
      addEventListener: noop,
      removeEventListener: noop,
      createElement: function(tag){
        return {
          tagName: String(tag || "").toUpperCase(),
          style: {},
          setAttribute: noop,
          appendChild: noop,
          onload: null,
          onreadystatechange: null,
          readyState: "complete",
        };
      },
      getElementsByTagName: function(){ return [{ appendChild: noop }]; },
      querySelector: function(){ return null; },
      querySelectorAll: function(){ return []; },
      documentElement: { clientWidth: 1920, clientHeight: 1080 },
      body: { clientWidth: 1920, clientHeight: 1080 },
    },
    performance: { now: function(){ return Date.now(); } },
    localStorage: { getItem: function(){ return null; }, setItem: noop, removeItem: noop },
    sessionStorage: { getItem: function(){ return null; }, setItem: noop, removeItem: noop },
  };
  sandbox.window = sandbox;
  sandbox.global = sandbox;
  sandbox.self = sandbox;
  sandbox.globalThis = sandbox;
  return sandbox;
}

function make_fanqie_params(baseUrl, sdkPath, userAgent, referer, tokenLen) {
  const msToken = generateMsToken(tokenLen || 132);
  const sdkCode = fs.readFileSync(sdkPath, "utf8");
  const sandbox = createSandbox(
    userAgent || "Mozilla/5.0",
    referer || "https://fanqienovel.com/",
    msToken
  );
  vm.createContext(sandbox);
  vm.runInContext(sdkCode, sandbox, { timeout: 10000 });
  if (!sandbox.byted_acrawler || typeof sandbox.byted_acrawler.frontierSign !== "function") {
    throw new Error("byted_acrawler.frontierSign not found");
  }
  const signObj = sandbox.byted_acrawler.frontierSign(baseUrl);
  const aBogus = (signObj && (signObj["X-Bogus"] || signObj["a_bogus"])) || "";
  if (!aBogus) throw new Error("failed to generate a_bogus");
  return { msToken: msToken, a_bogus: String(aBogus) };
}
"""


def ensure_sdk(sdk_path: pathlib.Path) -> None:
    if sdk_path.exists():
        return
    resp = requests.get(DEFAULT_SDK_URL, headers={"User-Agent": DEFAULT_UA}, timeout=20)
    resp.raise_for_status()
    sdk_path.write_text(resp.text, encoding="utf-8")


def build_base_url(input_url: str) -> str:
    split = urlsplit(input_url)
    pairs = parse_qsl(split.query, keep_blank_values=True)
    filtered = [(k, v) for (k, v) in pairs if k not in {"msToken", "a_bogus"}]
    query = urlencode(filtered, doseq=True)
    return urlunsplit((split.scheme, split.netloc, split.path, query, split.fragment))


def main() -> int:
    parser = argparse.ArgumentParser(description="Fanqie API request via Python + execjs")
    parser.add_argument("url", help="API URL (with or without msToken/a_bogus)")
    parser.add_argument("--sdk-path", default="webmssdk.js", help="local webmssdk.js path")
    parser.add_argument("--token-len", type=int, default=132, help="msToken random body length")
    parser.add_argument("--timeout", type=int, default=20, help="request timeout seconds")
    parser.add_argument("--insecure", action="store_true", help="disable TLS cert verification")
    args = parser.parse_args()

    sdk_path = pathlib.Path(args.sdk_path).resolve()
    ensure_sdk(sdk_path)

    base_url = build_base_url(args.url)
    ctx = execjs.compile(JS_BRIDGE)
    params = ctx.call(
        "make_fanqie_params",
        base_url,
        str(sdk_path),
        DEFAULT_UA,
        DEFAULT_REFERER,
        args.token_len,
    )

    if args.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    req = requests.get(
        base_url,
        params={"msToken": params["msToken"], "a_bogus": params["a_bogus"]},
        headers={"User-Agent": DEFAULT_UA, "Referer": DEFAULT_REFERER, "Accept": "application/json, text/plain, */*"},
        timeout=args.timeout,
        verify=not args.insecure,
    )
    req.raise_for_status()

    try:
        data = req.json()
    except Exception:
        data = None

    output = {
        "status": req.status_code,
        "request_url": req.url,
        "msToken": params["msToken"],
        "a_bogus": params["a_bogus"],
        "code": data.get("code") if isinstance(data, dict) else None,
        "has_data": bool(isinstance(data, dict) and data.get("data") is not None),
        "preview": req.text[:200],
    }
    print(json.dumps(output, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.HTTPError as exc:
        print(f"HTTPError: {exc}", file=sys.stderr)
        if exc.response is not None:
            print(exc.response.text[:1000], file=sys.stderr)
        raise
