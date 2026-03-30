const url = process.argv[2];

if (!url) {
  console.error("Usage: node inspect_page.js <url>");
  process.exit(1);
}

(async () => {
  const res = await fetch(url, { headers: { "user-agent": "Mozilla/5.0" } });
  const txt = await res.text();

  const mTitle = txt.match(/<title>([\s\S]*?)<\/title>/i);
  const mDesc = txt.match(/<meta[^>]+name="description"[^>]+content="([\s\S]*?)"/i);
  const mKeywords = txt.match(/<meta[^>]+name="keywords"[^>]+content="([\s\S]*?)"/i);

  console.log("status", res.status);
  console.log("title", mTitle ? mTitle[1].slice(0, 200) : "");
  console.log("description", mDesc ? mDesc[1].slice(0, 200) : "");
  console.log("keywords", mKeywords ? mKeywords[1].slice(0, 200) : "");
})();

