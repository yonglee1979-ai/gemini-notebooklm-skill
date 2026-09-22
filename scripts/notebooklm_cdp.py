#!/usr/bin/env python3
"""NotebookLM CDP automation.

Subcommands:
  deck      Download a Studio slide-deck PDF from a NotebookLM notebook.
  watermark Upload a PDF to notebooklmwatermark.com/zh, strip the watermark, download it.

All inputs are passed as arguments; nothing sensitive is hard-coded.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp_common as C  # noqa: E402


def cmd_deck(args):
    p, browser, ctx, page, ws_url = C.connect(args.port)
    try:
        page.goto(args.url, wait_until="load", timeout=40000)
        page.wait_for_timeout(6000)
        page.keyboard.press("Escape")
        page.wait_for_timeout(800)

        # CRITICAL: set download behavior AFTER connect.
        C.set_download_behavior(ws_url, args.out)
        before = C._dir_snapshot([args.out, os.path.expanduser("~/Downloads")])

        # Reveal the Studio panel: scroll scrollable regions on the right (x>700) to bottom.
        page.evaluate(
            """() => {
                [...document.querySelectorAll('*')].forEach(el => {
                    const s = getComputedStyle(el);
                    const r = el.getBoundingClientRect();
                    if (r.x > 700 && r.width > 200 && el.scrollHeight > el.clientHeight + 50 &&
                        (s.overflowY === 'auto' || s.overflowY === 'scroll')) {
                        el.scrollTop = el.scrollHeight;
                    }
                });
            }"""
        )
        time.sleep(1)

        # Open the deck card's "more" menu (title element with no children, matching text).
        page.evaluate(
            """(title) => {
                const els = [...document.querySelectorAll('*')].filter(el =>
                    el.children.length === 0 && el.textContent.trim() === title &&
                    (() => { const r = el.getBoundingClientRect();
                             return r.x > 700 && r.y > 0 && r.y < window.innerHeight; })());
                if (!els.length) throw new Error('deck title not visible');
                let cur = els[0];
                for (let i=0;i<12 && cur.parentElement;i++){
                    cur = cur.parentElement;
                    const btns = [...cur.querySelectorAll('button')].filter(bb => {
                        const lbl = bb.getAttribute('aria-label')||'';
                        return (lbl.includes('更多')||lbl.toLowerCase().includes('more')) &&
                               bb.getBoundingClientRect().width>0;
                    });
                    if (btns.length) { btns[0].click(); return; }
                }
                throw new Error('menu button not found');
            }""",
            args.deck_title,
        )
        time.sleep(1.5)

        items = page.evaluate(
            """() => [...document.querySelectorAll('button, [role=menuitem]')].map(el => {
                const t = (el.textContent||'').trim();
                const r = el.getBoundingClientRect();
                return {text: t.replace(/\\s+/g,' '), x: Math.round(r.x+r.width/2),
                        y: Math.round(r.y+r.height/2), visible: r.width>0 && r.height>0};
            }).filter(i => i.text.includes('下载'));"""
        )
        target = next((it for it in items if "PDF" in it["text"] and it["visible"]), None)
        if not target:
            print("ERROR: PDF download item not found. Menu items:", items, file=sys.stderr)
            return 1
        page.mouse.click(target["x"], target["y"])
        print(f"Clicked PDF download item: {target['text']}")

        fp = C.wait_for_new_file(before, timeout=args.timeout,
                                 watch_dirs=[args.out, os.path.expanduser("~/Downloads")])
        if fp:
            print(f"DOWNLOADED: {fp} ({os.path.getsize(fp)/1024:.0f} KB)")
            return 0
        print("ERROR: no file appeared", file=sys.stderr)
        return 2
    finally:
        browser.close()
        p.stop()


def cmd_watermark(args):
    p, browser, ctx, page, ws_url = C.connect(args.port)
    try:
        page.goto(args.site, wait_until="load", timeout=40000)
        page.wait_for_timeout(5000)
        C.set_download_behavior(ws_url, args.out)
        before = C._dir_snapshot([args.out, os.path.expanduser("~/Downloads")])

        inp = page.locator("input[type=file]").first
        inp.wait_for(state="visible", timeout=20000)
        inp.set_input_files(args.pdf)
        print("Uploaded:", args.pdf)
        time.sleep(5)

        # Click "清理 PDF" (clean / process).
        clean = page.locator("text=清理 PDF >> visible=true").first
        clean.scroll_into_view_if_needed()
        clean.click()
        print("Clicked 清理 PDF")

        # Poll for the download button (re-rasterization is fast for ~20 pages).
        end = time.time() + args.timeout
        dl = None
        while time.time() < end:
            items = C.visible_buttons(page, ("下载", "水印", "Download"))
            dl = next((i for i in items
                       if "下载" in i["text"] and "水印" in i["text"]), None)
            if dl:
                break
            time.sleep(6)
        if not dl:
            print("ERROR: download button did not appear", file=sys.stderr)
            return 2

        page.mouse.click(dl["x"] + dl["w"] // 2, dl["y"] + dl["h"] // 2)
        print(f"Clicked download: {dl['text']}")

        fp = C.wait_for_new_file(before, timeout=args.timeout,
                                 watch_dirs=[args.out, os.path.expanduser("~/Downloads")])
        if fp:
            dst = os.path.join(args.out, "dewatermarked.pdf")
            if os.path.abspath(fp) != os.path.abspath(dst):
                if os.path.exists(dst):
                    dst = os.path.join(args.out, "dewatermarked_2.pdf")
                os.rename(fp, dst)
                fp = dst
            print(f"DOWNLOADED: {fp} ({os.path.getsize(fp)/1024:.0f} KB)")
            return 0
        print("ERROR: no file downloaded", file=sys.stderr)
        return 3
    finally:
        browser.close()
        p.stop()


def build_parser():
    ap = argparse.ArgumentParser(description="NotebookLM CDP automation")
    ap.add_argument("--port", type=int, default=9222)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("deck", help="Download a Studio deck PDF")
    d.add_argument("--url", required=True, help="NotebookLM notebook URL")
    d.add_argument("--deck-title", required=True, help="Exact Studio deck title text")
    d.add_argument("--out", default="./out")
    d.add_argument("--timeout", type=int, default=420)
    d.set_defaults(func=cmd_deck)

    w = sub.add_parser("watermark", help="Strip watermark from a PDF")
    w.add_argument("--pdf", required=True, help="Local PDF path to clean")
    w.add_argument("--site", default="https://www.notebooklmwatermark.com/zh")
    w.add_argument("--out", default="./out")
    w.add_argument("--timeout", type=int, default=600)
    w.set_defaults(func=cmd_watermark)
    return ap


if __name__ == "__main__":
    args = build_parser().parse_args()
    raise SystemExit(args.func(args) or 0)
