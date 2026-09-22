"""Shared CDP helpers for NotebookLM automation.

No secrets, tokens, or machine-specific values are hard-coded. The Chrome
DevTools WebSocket endpoint is auto-discovered from the debug port.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import websocket
from playwright.sync_api import sync_playwright


def get_browser_ws(port: int = 9222, host: str = "127.0.0.1") -> str:
    """Auto-discover the browser-level DevTools WebSocket URL (rotates per launch)."""
    with urllib.request.urlopen(f"http://{host}:{port}/json/version", timeout=10) as r:
        data = json.loads(r.read())
    return data["webSocketDebuggerUrl"]


def connect(port: int = 9222):
    """connect_over_cdp and return (playwright, browser, context, page, ws_url)."""
    ws_url = get_browser_ws(port)
    p = sync_playwright().start()
    browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
    ctx = browser.contexts[0]
    page = ctx.new_page()
    return p, browser, ctx, page, ws_url


def set_download_behavior(ws_url: str, download_dir: str):
    """Best-effort: route downloads to `download_dir`.

    MUST be called AFTER connect_over_cdp, otherwise Playwright resets it.
    Some Chrome states (no page targets / browser-context model) reject the
    browser-level command with "Browser context management is not supported".
    In that case we silently fall back to the browser's default download
    directory — `wait_for_new_file` also watches ~/Downloads, so the file is
    still captured. For a deterministic path, launch Chrome with
    `--download-default-directory` (see launch_chrome_cdp.sh).
    """
    os.makedirs(download_dir, exist_ok=True)
    try:
        ws = websocket.create_connection(ws_url, timeout=15)
        ws.send(json.dumps({
            "id": 1,
            "method": "Browser.setDownloadBehavior",
            "params": {"behavior": "allow", "downloadPath": download_dir, "eventsEnabled": True},
        }))
        ws.recv()
        ws.close()
        return ws
    except Exception as e:  # pragma: no cover - environment dependent
        print(f"WARNING: Browser.setDownloadBehavior failed ({e}); "
              f"falling back to default download dir (also watched).", file=sys.stderr)
        return None


def _dir_snapshot(watch_dirs) -> dict:
    files = {}
    for d in watch_dirs:
        try:
            for f in os.listdir(d):
                fp = os.path.join(d, f)
                if os.path.isfile(fp):
                    files[fp] = os.path.getmtime(fp)
        except OSError:
            pass
    return files


def wait_for_new_file(before: dict, timeout: int = 300, watch_dirs=None) -> str | None:
    """Wait for a stable, non-hidden final file not present in `before`."""
    watch_dirs = watch_dirs or []
    end = time.time() + timeout
    while time.time() < end:
        now = _dir_snapshot(watch_dirs)
        for fp in now:
            name = os.path.basename(fp)
            if fp in before:
                continue
            if name.startswith(".") or name.endswith(".crdownload"):
                continue  # Chrome temp / partial
            try:
                s1 = os.path.getsize(fp)
                time.sleep(2)
                s2 = os.path.getsize(fp)
            except OSError:
                continue  # temp file vanished mid-check
            if s1 == s2 and s1 > 0:
                return fp
        time.sleep(2)
    return None


def visible_buttons(page, keywords=("下载", "清理", "处理", "完成", "保存", "Download", "水印")):
    """Return visible button/a/role=button texts with their rects (viewport-relative)."""
    return page.evaluate(
        """(kws) => {
            const out = [];
            [...document.querySelectorAll('button, a, [role=button]')].forEach(el => {
                const t = (el.textContent||'').trim().replace(/\\s+/g,' ');
                const r = el.getBoundingClientRect();
                if (t && r.width>0 && r.height>0 && r.top < window.innerHeight + 300 && r.left >= 0 && t.length < 60) {
                    if (kws.some(k => t.includes(k))) {
                        out.push({text: t, x: Math.round(r.x), y: Math.round(r.y),
                                  w: Math.round(r.width), h: Math.round(r.height)});
                    }
                }
            });
            return out;
        }""",
        list(keywords),
    )
