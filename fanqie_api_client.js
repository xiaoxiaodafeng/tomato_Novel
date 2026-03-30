#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const DEFAULT_SDK_URL = "https://lf3-cdn-tos.bytescm.com/obj/rc-web-sdk/webmssdk.js";
const DEFAULT_UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

function randomFromCharset(length, charset) {
  let out = "";
  for (let i = 0; i < length; i += 1) {
    const idx = Math.floor(Math.random() * charset.length);
    out += charset[idx];
  }
  return out;
}

function generateMsToken(length = 132) {
  const charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
  return `${randomFromCharset(length, charset)}==`;
}

function normalizeBaseUrl(inputUrl) {
  const url = new URL(inputUrl);
  url.searchParams.delete("msToken");
  url.searchParams.delete("a_bogus");
  return url;
}

function createNoopBrowserSandbox({ userAgent, referer, msToken }) {
  const noop = () => {};
  const immediateTimeout = (fn) => {
    try {
      if (typeof fn === "function") fn();
    } catch (_) {
      // ignore internal sdk timer errors
    }
    return 0;
  };

  const sandbox = {
    console,
    Buffer,
    URL,
    URLSearchParams,
    TextEncoder,
    TextDecoder,
    crypto: globalThis.crypto,
    fetch: globalThis.fetch,
    Request: globalThis.Request,
    Response: globalThis.Response,
    Headers: globalThis.Headers,
    atob: globalThis.atob,
    btoa: globalThis.btoa,
    setTimeout: immediateTimeout,
    clearTimeout: noop,
    setInterval: () => 0,
    clearInterval: noop,
    XMLHttpRequest: function XMLHttpRequest() {},
    location: {
      href: "https://fanqienovel.com/",
      origin: "https://fanqienovel.com",
      hostname: "fanqienovel.com",
      protocol: "https:",
      host: "fanqienovel.com",
      pathname: "/",
    },
    navigator: {
      userAgent,
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
      cookie: `xmst=${msToken}`,
      hidden: false,
      visibilityState: "visible",
      addEventListener: noop,
      removeEventListener: noop,
      createElement: (tag) => ({
        tagName: String(tag || "").toUpperCase(),
        style: {},
        setAttribute: noop,
        appendChild: noop,
        onload: null,
        onreadystatechange: null,
        readyState: "complete",
      }),
      getElementsByTagName: () => [{ appendChild: noop }],
      querySelector: () => null,
      querySelectorAll: () => [],
      documentElement: { clientWidth: 1920, clientHeight: 1080 },
      body: { clientWidth: 1920, clientHeight: 1080 },
    },
    performance: { now: () => Date.now() },
    localStorage: { getItem: () => null, setItem: noop, removeItem: noop },
    sessionStorage: { getItem: () => null, setItem: noop, removeItem: noop },
  };

  sandbox.window = sandbox;
  sandbox.global = sandbox;
  sandbox.self = sandbox;
  sandbox.globalThis = sandbox;
  return sandbox;
}

async function ensureWebMsSdk(sdkPath, sdkUrl) {
  if (fs.existsSync(sdkPath)) return;
  const res = await fetch(sdkUrl, { headers: { "user-agent": DEFAULT_UA } });
  if (!res.ok) {
    throw new Error(`download webmssdk failed: ${res.status} ${res.statusText}`);
  }
  const code = await res.text();
  fs.writeFileSync(sdkPath, code, "utf8");
}

function generateABogus(baseUrl, sdkCode, msToken, userAgent, referer) {
  const sandbox = createNoopBrowserSandbox({ userAgent, referer, msToken });
  vm.createContext(sandbox);
  vm.runInContext(sdkCode, sandbox, { timeout: 10_000 });
  if (!sandbox.byted_acrawler || typeof sandbox.byted_acrawler.frontierSign !== "function") {
    throw new Error("byted_acrawler.frontierSign not found");
  }
  const signObj = sandbox.byted_acrawler.frontierSign(baseUrl);
  const aBogus = signObj && (signObj["X-Bogus"] || signObj["a_bogus"]);
  if (!aBogus) {
    throw new Error(`frontierSign returned invalid value: ${JSON.stringify(signObj)}`);
  }
  return String(aBogus);
}

async function requestWithTokens(baseUrl, msToken, aBogus, userAgent, referer) {
  const finalUrl = new URL(baseUrl.toString());
  finalUrl.searchParams.set("msToken", msToken);
  finalUrl.searchParams.set("a_bogus", aBogus);

  const res = await fetch(finalUrl.toString(), {
    headers: {
      "user-agent": userAgent,
      referer,
      accept: "application/json, text/plain, */*",
    },
  });
  const text = await res.text();

  let json = null;
  try {
    json = JSON.parse(text);
  } catch (_) {
    // keep raw text
  }

  return {
    status: res.status,
    ok: res.ok,
    url: finalUrl.toString(),
    json,
    text,
  };
}

async function main() {
  const inputUrl = process.argv[2];
  if (!inputUrl) {
    console.error("Usage: node fanqie_api_client.js \"<api_url_without_or_with_msToken_a_bogus>\"");
    process.exit(1);
  }

  const sdkPath = path.resolve(__dirname, "webmssdk.js");
  await ensureWebMsSdk(sdkPath, DEFAULT_SDK_URL);
  const sdkCode = fs.readFileSync(sdkPath, "utf8");

  const baseUrl = normalizeBaseUrl(inputUrl);
  const referer = "https://fanqienovel.com/";
  const userAgent = DEFAULT_UA;
  const msToken = generateMsToken();
  const aBogus = generateABogus(baseUrl.toString(), sdkCode, msToken, userAgent, referer);

  const result = await requestWithTokens(baseUrl, msToken, aBogus, userAgent, referer);
  const summary = {
    msToken,
    a_bogus: aBogus,
    status: result.status,
    ok: result.ok,
    code: result.json && Object.prototype.hasOwnProperty.call(result.json, "code") ? result.json.code : null,
    has_data: Boolean(result.json && result.json.data),
    request_url: result.url,
  };

  console.log(JSON.stringify(summary, null, 2));
  if (!result.ok) {
    console.error(result.text.slice(0, 1000));
    process.exit(2);
  }
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
});

