# gemini-notebooklm skill

Read, analyze, and download Google **NotebookLM** ("Gemini Notebook") notebooks
and their Studio slide decks, including a full literature→outline→deck→PDF
delivery flow and a CDP-based watermark-removal step.

This is a [WorkBuddy](https://www.workbuddy.cn) skill. It drives an
already-authenticated Chrome instance over the Chrome DevTools Protocol (CDP)
through Playwright — it does **not** use any NotebookLM API key or third-party
extension.

## Security

- No personal notebook URLs, Google account emails, auth tokens, or absolute
  local paths are stored in this repo. Everything sensitive is passed as a
  command-line argument or auto-discovered at runtime.
- The Chrome DevTools WebSocket id rotates on every launch; the scripts fetch it
  from `http://127.0.0.1:<port>/json/version`, so no per-machine value is
  committed.
- Keep the user's real Chrome profile untouched — launch a separate debug-profile
  Chrome (see `scripts/launch_chrome_cdp.sh`).

## Prerequisites

- Chrome/Chromium with remote debugging on a throwaway profile.
- Python 3.10+ with `playwright` (browser installed), `websocket-client`,
  `pypdf`, `pymupdf`:
  ```bash
  python -m venv venv && venv/bin/pip install playwright websocket-client pypdf pymupdf
  venv/bin/python -m playwright install chromium
  ```

## Install into WorkBuddy

Copy this repo's contents into a skill folder:
```bash
SKILL_DIR="$HOME/.workbuddy/skills/gemini-notebooklm"
mkdir -p "$SKILL_DIR"
cp -R SKILL.md scripts "$SKILL_DIR/"
```
Restart WorkBuddy (or reload skills). The skill becomes available as
`gemini-notebooklm`.

## Usage

1. Launch a debug Chrome (on the user's machine):
   ```bash
   bash scripts/launch_chrome_cdp.sh 9222 "$HOME/chrome-cdp-profile"
   ```
2. Download a Studio deck PDF:
   ```bash
   venv/bin/python scripts/notebooklm_cdp.py deck \
     --url "https://notebook.google.com/notebook/<ID>" \
     --deck-title "Your Deck Title" --out ./out
   ```
3. Strip the NotebookLM watermark (PDF only):
   ```bash
   venv/bin/python scripts/notebooklm_cdp.py watermark \
     --pdf ./out/deck.pdf --out ./out
   ```
4. (Optional) Extract the generated outline:
   ```bash
   venv/bin/python scripts/extract_outline.py \
     --url "https://notebook.google.com/notebook/<ID>" --out outline.md
   ```

## Notes / gotchas

- Call `Browser.setDownloadBehavior` **after** `connect_over_cdp`, or Playwright
  silently resets it and downloads land in `~/Downloads`.
- Studio "下载" menu items respond to coordinate clicks, not locator clicks.
- Deck generation in Studio takes ~5–10 minutes; poll with a long timeout.
- If `connect_over_cdp` fails with `Browser context management is not supported`,
  your Chrome is in a multi-context state and rejects the browser-level download
  command. Relaunch a **fresh** debug-profile Chrome with `launch_chrome_cdp.sh`
  (single clean context) and retry. The scripts also watch `~/Downloads` as a
  fallback and can launch Chrome with `DOWNLOAD_DIR=...` for a deterministic path.
