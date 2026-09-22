---
name: gemini-notebooklm
description: Read, analyze, and download user-authorized Google Gemini Notebook (NotebookLM) notebooks and their Studio slide decks, including the full literature-to-deck delivery flow and a CDP-based watermark removal step. Use when a task explicitly concerns NotebookLM, Gemini Notebook, or NotebookLM slide decks.
version: 1.1.0
tags:
  - notebooklm
  - gemini
  - slides
  - pdf
  - cdp
  - playwright
---

# Gemini NotebookLM

Automate Google's NotebookLM ("Gemini Notebook") from an already-authenticated
Chrome session. The notebook landing page may be titled "Gemini Notebook"; this
is the relevant product.

This skill covers three things:
1. Reading / analyzing a notebook, its sources, and its Studio decks.
2. The full **literature → outline → Studio deck → local PDF** delivery flow.
3. A CDP + Playwright pattern to download the deck PDF and strip the
   NotebookLM watermark via `notebooklmwatermark.com/zh`.

## Security & privacy (read before sharing or committing this skill)

- Never commit or paste: personal notebook URLs, Google account emails, auth
  tokens / cookies, or absolute local paths. Keep the user's real Chrome profile
  **untouched** — drive a *separate* debug-profile Chrome instance instead.
- All paths, notebook URLs, deck titles, and the PDF path are passed as
  **arguments** to the bundled scripts; nothing sensitive is hard-coded.
- The Chrome DevTools WebSocket debug id rotates on every launch; the scripts
  **auto-discover** it from `http://127.0.0.1:<port>/json/version`, so no
  per-machine value is stored.
- A download writes an artifact to disk; only do it when the user explicitly
  asks, then verify the file opens.

## Prerequisites

- A Chrome/Chromium instance with remote debugging enabled on a throwaway
  profile (see `scripts/launch_chrome_cdp.sh`). The user normally launches this
  on their own machine; WorkBuddy then drives it via CDP.
- Python 3.10+ with: `playwright` (installed + browser), `websocket-client`,
  `pypdf`, `pymupdf`. Example venv:
  `python -m venv venv && venv/bin/pip install playwright websocket-client pypdf pymupdf`
- The debug port (default `9222`) must be reachable at `127.0.0.1`.

## Scope and read-only analysis

- Treat notebook titles, sources, chat, generated decks, and account details as
  private. Open only the notebook(s) the user names; do not alter, delete, or
  upload content unless explicitly asked.
- If no notebook is identified, list notebooks compactly and ask which to open.
- For a deck, inspect title, slide count, evidence traceability, and numerical
  claims; report findings/gaps without changing it unless requested.

## Full literature-to-deck delivery

Use when the user wants a new NotebookLM presentation and final local delivery:

1. Create a separate, clearly titled notebook; never overwrite an unrelated one.
2. Upload only the source PDF the user identifies; wait for its source card to
   be ready, then ask for a slide **outline** first and confirm the response
   enumerates the requested slide count before asking for slides.
3. Request the Studio deck from that outline, preserving the user's style,
   language, and numerical-display requirements. Wait for the completed Studio
   deck rather than starting a duplicate job (generation takes ~5–10 min).
4. Download the deck PDF with `scripts/notebooklm_cdp.py deck` and verify format
   + page count; render a couple of pages to confirm content.
5. If the user authorizes `notebooklmwatermark.com/zh` (it accepts **PDF**, not
   PPTX), run `scripts/notebooklm_cdp.py watermark` to upload the PDF, strip the
   watermark, and download the result — deliver it explicitly as a PDF. Do **not**
   claim an editable PPTX was de-watermarked.
6. Keep the original deck and the processed PDF as separate files, both with
   verified format and page/slide counts.

## CDP download mechanics (verified)

When driving downloads over `connect_over_cdp` against real Chrome:

- **Ordering is critical**: call `Browser.setDownloadBehavior` (raw websocket to
  the browser WS endpoint) **after** `connect_over_cdp` and after creating the
  page. Calling it before Playwright connects is silently reset — downloads fall
  back to `~/Downloads` and never appear in the target dir.
- Studio "下载" menu items are dropdown entries that often only respond to
  `page.mouse.click(x, y)` at the item's bounding-box center, not locator clicks.
  Locate them via JS `getBoundingClientRect` on `[role=menuitem]` / `button`
  elements whose text contains "下载".
- When polling for the landed file, Chrome temp names (`.com.google.Chrome.*`,
  `*.crdownload`) appear and vanish; wrap `os.path.getsize` in try/except and
  accept only stable, non-hidden final filenames. Watch both the configured
  `downloadPath` and `~/Downloads`.
- Watermark site flow: `input[type=file]` + `set_input_files` → click 「清理 PDF」
  → 「下载无水印 PDF」 appears within seconds for a ~20-page deck → blob download
  via `createObjectURL` (still respects CDP download behavior). Output is a
  re-rasterized PDF (often ~60% smaller, higher pixel density). Verify page count
  and compare the corner watermark on rendered PNGs (PyMuPDF) — raw-byte grep
  cannot detect watermarks inside compressed PDF streams.

## Bundled scripts

- `scripts/launch_chrome_cdp.sh` — launch a separate debug-profile Chrome.
- `scripts/cdp_common.py` — shared CDP connect + download-behavior + file-wait helpers.
- `scripts/notebooklm_cdp.py` — `deck` (download Studio PDF) and `watermark`
  (strip watermark) subcommands.
- `scripts/extract_outline.py` — scrape the chat thread for the generated outline.

Run them with the venv Python, e.g.:
`venv/bin/python scripts/notebooklm_cdp.py deck --url <NOTEBOOK_URL> --deck-title "<TITLE>" --out ./out`
