# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An MCP (Model Context Protocol) server that generates images by controlling ChatGPT's web interface via Playwright. Uses a **dedicated Chrome profile** (`./chrome-profile/`) so the user's daily Chrome is never affected — it can be open or closed.

## Commands

```bash
uv run python init_auth.py   # First-time: open Chrome, log into ChatGPT manually
uv run python test_server.py # Test generate_image() directly (bypasses MCP layer)
uv run python server.py      # Run the MCP server (normally spawned by Claude Code)
```

## Architecture

Two layers, single file each:

- **`server.py`** — MCP server + Playwright automation in one file.
  - `generate_image(prompt, output_dir) -> Path`: sync function that drives Chrome, called from async MCP handlers via `asyncio.run()`.
  - MCP layer: raw `mcp` SDK (`Server`, `stdio_server`, `types`), stdio transport.
  - Flow: navigate `https://chatgpt.com/images` → type prompt into `#prompt-textarea` (ProseMirror editor) → click `[data-testid='send-button']` → wait for `img[alt*="已生成图片"]` → download via authenticated `fetch()` in page context → save to `output_dir`.

- **`init_auth.py`** — Opens Chrome with the dedicated profile, navigates to ChatGPT, then waits for user to press ESC in the browser. The auth state persists in the profile for subsequent MCP calls.

- **`test_server.py`** — Calls `generate_image()` directly, bypassing the MCP layer. Output goes to `./test-output/`.

### Key selectors

| Element | Selector |
|---|---|
| Prompt input | `#prompt-textarea` (ProseMirror, `role="textbox"`) |
| Send button | `[data-testid="send-button"]` |
| Generated image | `img[alt*="已生成图片"]` (Chinese UI) or `img[alt*="Generated image"]` (English) |
| Image container | `div.group\/imagegen-image` |
| Image src pattern | `https://chatgpt.com/backend-api/estuary/content?id=file_xxx` |

## Tech Stack

- Python 3.12+, managed with uv
- `playwright` (sync API, system Chrome via `channel="chrome"`)
- `mcp` Python SDK (low-level `Server`, `stdio_server`, `types`)
- `[tool.uv] package = false` — not a buildable package, just a script project

## Installation

### 1. First-time auth

```bash
uv run python init_auth.py
```

Opens Chrome with `./chrome-profile/`. Log into ChatGPT manually, then press ESC in the browser to close.

### 2. Register the MCP server

Run from the project root:

```bash
claude mcp add --transport stdio image-gen --scope user -- uv run --project "$(pwd)" server.py
```

Writes to `~/.claude.json` (user scope, available across all projects). `$(pwd)` ensures the stored path is absolute. Claude Code spawns the server on demand via stdio and the process exits after each call.

### 3. Test

```bash
uv run python test_server.py
```

## Design Decisions

- **Chrome profile**: Dedicated `./chrome-profile/`, isolated from user's daily browsing. Chrome's exclusive profile lock means concurrent MCP calls are not supported — requests are handled sequentially.
- **Chrome automation flag**: `--disable-blink-features=AutomationControlled` suppresses the "automated test software" infobar.
- **Launch model**: On-demand child process. Claude Code spawns the server per invocation; the process exits after the call.
- **Execution model**: Synchronous — blocks until the image is saved, returns the file path.
- **Image download**: Uses `page.evaluate()` to `fetch()` the image URL inside the authenticated page context (data URL → base64 decode → write to disk), avoiding the need to manage cookies externally.
