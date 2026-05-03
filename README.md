[English](README.md) | [简体中文](README.zh-CN.md)

# image-gen

MCP server that generates images via ChatGPT's web interface using Playwright. Intended for use with Claude Code — Claude can generate images by invoking the `generate_image` tool.

## How it works

This server launches Chrome with a dedicated profile, navigates to ChatGPT's image generation page, types in your prompt, and downloads the resulting image. Each invocation starts its own Chrome process and exits when done.

The dedicated profile (`./chrome-profile/`) is isolated from your daily Chrome — you authenticate once and subsequent calls reuse the session.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Chrome installed (macOS: `/Applications/Google Chrome.app`)
- A ChatGPT account (free tier works, but Plus has higher rate limits)

## Setup

> **Important**: `cd` into the project directory first. After installation, do not move or rename this directory — Claude Code relies on the absolute path registered in step 3.

### 1. Install dependencies

```bash
uv sync
playwright install chromium
```

### 2. Log into ChatGPT

```bash
uv run python init_auth.py
```

This opens Chrome. Log into ChatGPT manually, then press **ESC** in the browser to close. Your auth state persists in `./chrome-profile/`.

### 3. Register with Claude Code

```bash
claude mcp add --transport stdio image-gen --scope user -- uv run --project "$(pwd)" "$(pwd)/server.py"
```

### 4. Test (optional)

```bash
uv run python test_server.py
```

Generates a test image to `./test-output/` without going through the MCP layer.

## Usage in Claude Code

Once registered, Claude can call the `generate_image` tool with a prompt and output directory. Example prompt to Claude:

> Generate an image of a cat sleeping on a cloud and save it to ~/Desktop

## Limitations

- **Single instance**: Chrome locks the profile exclusively — concurrent calls are not supported.
- **ChatGPT rate limits**: Free tier has limited image generation capacity; Plus has higher limits.
- **UI-dependent**: ChatGPT's UI selectors may change over time. The key selectors are documented in `CLAUDE.md`.
- **macOS only**: Uses `channel="chrome"` which assumes the standard macOS Chrome path.
