#!/usr/bin/env python3
"""Scrape the generated slide outline from a NotebookLM chat thread.

NotebookLM renders the outline as chat text. This scrolls the thread to the top,
grabs the page text, and cuts it at the first "Slide N" marker, trimming the
trailing chat-UI noise (buttons like keep_pin / copy_all / thumb_up).

Usage:
  python extract_outline.py --url <NOTEBOOK_URL> --out outline.md [--port 9222]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp_common as C  # noqa: E402


UI_NOISE = ("keep_pin", "copy_all", "thumb_up", "thumb_down", "expand_more",
            "下一步确认与生成方案", "方案 A", "方案 B")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", default="outline.md")
    ap.add_argument("--port", type=int, default=9222)
    args = ap.parse_args()

    p, browser, ctx, page, _ = C.connect(args.port)
    try:
        page.goto(args.url, wait_until="load", timeout=40000)
        page.wait_for_timeout(5000)

        # Scroll the chat thread to the very top so all outline text is in the DOM.
        page.evaluate(
            """() => {
                [...document.querySelectorAll('*')].forEach(el => {
                    const s = getComputedStyle(el);
                    if ((s.overflowY === 'auto' || s.overflowY === 'scroll') &&
                        el.scrollHeight > el.clientHeight + 50) {
                        el.scrollTop = 0;
                    }
                });
                window.scrollTo(0, 0);
            }"""
        )
        time.sleep(2)
        text = page.evaluate("() => document.body.innerText")
    finally:
        browser.close()
        p.stop()

    # Cut at the first "Slide N" and stop before trailing chat-UI markers.
    m = re.search(r"Slide\s*\d+", text)
    if m:
        text = text[m.start():]
    for noise in UI_NOISE:
        idx = text.find(noise)
        if idx != -1:
            text = text[:idx]
    text = text.rstrip() + "\n"

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text)
    slides = len(re.findall(r"Slide\s*\d+", text))
    print(f"Wrote {args.out} ({slides} slide headers found)")


if __name__ == "__main__":
    main()
