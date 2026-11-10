"""Build every StepSheet output from one source: src/src.html.

    python3 src/build.py        (run from the repo root, or anywhere)

Produces, in the repo:
  StepSheet.html                      single-file offline app
  index.html + sw.js + manifest...    installable PWA (served by GitHub Pages)
  extension/app.js + editor.html      Chrome/Edge extension (manifest version bumped)
  python/stepsheet/static/StepSheet.html   bundled copy for the Python edition
  src/artifact.html                   copy for publishing as a claude.ai artifact

One source of truth: the web app, the PWA, the extension, and the Python
edition are all generated here, so they can never drift apart.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))   # .../src
ROOT = os.path.dirname(HERE)                         # repo root

def R(*p): return os.path.join(ROOT, *p)
def S(*p): return os.path.join(HERE, *p)

CACHE = "stepsheet-v20"   # bump when the app code changes so installed PWAs refresh

widths = open(S("widths.json"), encoding="utf-8").read().strip()
block = open(S("header-block.html"), encoding="utf-8").read().rstrip("\n")
src = open(S("src.html"), encoding="utf-8").read().replace("__WIDTHS__", widths)


def with_block(html):
    i = html.find("<head>")
    if i == -1:
        return html
    i += len("<head>")
    return html[:i] + "\n" + block + html[i:]


# ---- claude.ai artifact (generated; not served as a page) ----
open(S("artifact.html"), "w", encoding="utf-8").write(src)

# ---- single-file offline app: repo root + Python bundle (identical copies) ----
head = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '</head><body>')
stepsheet_html = with_block(head + src + "</body></html>")
open(R("StepSheet.html"), "w", encoding="utf-8").write(stepsheet_html)
os.makedirs(R("python", "stepsheet", "static"), exist_ok=True)
open(R("python", "stepsheet", "static", "StepSheet.html"), "w", encoding="utf-8").write(stepsheet_html)

# ---- browser extension ----
i = src.index("<script>"); j = src.rindex("</script>")
markup = src[:i].replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
js = src[i + 8:j]
style, body = markup.split("</style>", 1)
os.makedirs(R("extension"), exist_ok=True)
editor = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
          '<meta name="viewport" content="width=device-width,initial-scale=1">'
          '<link rel="icon" href="icons/icon32.png">' + style + "</style></head><body>"
          + body + '<script src="app.js"></script></body></html>')
open(R("extension", "editor.html"), "w", encoding="utf-8").write(with_block(editor))
open(R("extension", "app.js"), "w", encoding="utf-8").write(js)
mf = R("extension", "manifest.json")
m = json.load(open(mf)); v = list(map(int, m["version"].split("."))); v[1] += 1; v[2] = 0
m["version"] = ".".join(map(str, v)); json.dump(m, open(mf, "w"), indent=2)
print("extension", m["version"])

# ---- PWA (GitHub Pages serves the repo root) ----
pwa_head = ('<!doctype html><html lang="en"><head>'
            '<meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<meta name="apple-mobile-web-app-capable" content="yes">'
            '<meta name="mobile-web-app-capable" content="yes">'
            '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
            '<meta name="apple-mobile-web-app-title" content="StepSheet">'
            '<meta name="application-name" content="StepSheet">'
            '<meta name="theme-color" content="#232d3b">'
            '<link rel="apple-touch-icon" href="icon-180.png">'
            '<link rel="icon" type="image/png" href="icon-192.png">'
            '<link rel="manifest" href="manifest.webmanifest">'
            '</head><body>')
sw_reg = ("\n<script>if('serviceWorker' in navigator){window.addEventListener('load',function(){"
          "navigator.serviceWorker.register('sw.js').catch(function(){});});}</script>\n")
open(R("index.html"), "w", encoding="utf-8").write(with_block(pwa_head + src + sw_reg + "</body></html>"))

open(R("manifest.webmanifest"), "w", encoding="utf-8").write('''{
  "name": "StepSheet",
  "short_name": "StepSheet",
  "description": "Offline work-instruction editor and PDF exporter.",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "orientation": "any",
  "background_color": "#eef0f3",
  "theme_color": "#232d3b",
  "icons": [
    { "src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
    { "src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any" },
    { "src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
''')

open(R("sw.js"), "w", encoding="utf-8").write('''/* StepSheet offline cache. Bump CACHE when you update the app. */
const CACHE = "%s";
const ASSETS = ["./", "./index.html", "./manifest.webmanifest", "./icon-180.png", "./icon-192.png", "./icon-512.png"];
// cache:"reload" skips the browser's HTTP cache, so a new version never stores a stale page.
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS.map(u => new Request(u, { cache: "reload" })))).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
function timeout(ms) { return new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), ms)); }
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  const isPage = e.request.mode === "navigate" || (url.origin === location.origin && /(\\/|index\\.html)$/.test(url.pathname));
  if (isPage) {
    // The app page: newest copy when online (so updates show up on the next open), saved copy when offline or slow.
    e.respondWith(
      Promise.race([fetch(e.request, { cache: "no-store" }), timeout(4000)]).then(resp => {
        if (resp && resp.ok) { const copy = resp.clone(); caches.open(CACHE).then(c => c.put("./index.html", copy)); }
        return resp;
      }).catch(() => caches.match("./index.html").then(hit => hit || caches.match("./")))
    );
    return;
  }
  e.respondWith(
    caches.match(e.request).then(hit => hit || fetch(e.request).then(resp => {
      const copy = resp.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return resp;
    }).catch(() => caches.match("./index.html")))
  );
});
''' % CACHE)
print("pwa files written; cache", CACHE)
