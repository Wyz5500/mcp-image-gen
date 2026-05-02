"""MCP server that generates images via ChatGPT's web interface using Playwright.

Each invocation launches its own Chrome process with the dedicated profile,
creates a new tab, waits for image generation, downloads the result, then
cleans up and exits."""

import base64
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

PROFILE_DIR = Path(__file__).resolve().parent / "chrome-profile"


def generate_image(prompt: str, output_dir: Path) -> Path:
    """Core automation: drive ChatGPT to generate an image and save it locally.

    Returns the path to the saved image file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = context.new_page()

        # Step 1: Navigate to ChatGPT images
        page.goto("https://chatgpt.com/images")
        page.wait_for_selector("#prompt-textarea", timeout=30000)

        # Step 2: Type the prompt
        editor = page.locator("#prompt-textarea")
        editor.click()
        editor.fill(prompt)

        # Step 3: Submit
        page.locator("[data-testid='send-button']").click()

        # Step 4: Wait for the generated image
        # ChatGPT sets alt="已生成图片：..." on generated images (Chinese UI)
        # or "Generated image: ..." (English UI)
        page.wait_for_selector(
            'img[alt*="已生成图片"], img[alt*="Generated image"]',
            timeout=120000,
        )

        # Step 5: Locate the generated image and get its src
        gen_img = page.locator('img[alt*="已生成图片"], img[alt*="Generated image"]').first
        img_src = gen_img.get_attribute("src")

        # Step 6: Download the image via fetch in the authenticated page context
        img_data = page.evaluate(
            """async (url) => {
                const resp = await fetch(url);
                const blob = await resp.blob();
                return new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onloadend = () => resolve(reader.result);
                    reader.readAsDataURL(blob);
                });
            }""",
            img_src,
        )
        # img_data is a data: URL, extract the base64 part
        _, b64_data = img_data.split(",", 1)
        image_bytes = base64.b64decode(b64_data)

        # Step 7: Determine filename and save
        alt_text = gen_img.get_attribute("alt") or "generated-image"
        ext = ".png"
        filename = alt_text.replace("已生成图片：", "").replace("Generated image: ", "").strip()
        filename = filename.replace(" ", "_").replace("/", "_")[:80] or "image"
        filepath = output_dir / f"{filename}{ext}"

        filepath.write_bytes(image_bytes)

        page.close()
        context.close()

        return filepath


# --- MCP Server ---

server = Server("image-gen")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_image",
            description="Generate an image via ChatGPT. Takes a prompt and output directory, returns the path to the saved image.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The image generation prompt to send to ChatGPT",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Directory where the generated image will be saved",
                    },
                },
                "required": ["prompt", "output_dir"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.ContentBlock]:
    if name != "generate_image":
        raise ValueError(f"Unknown tool: {name}")

    prompt = arguments["prompt"]
    output_dir = Path(arguments["output_dir"])

    filepath = generate_image(prompt, output_dir)

    return [
        types.TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "filepath": str(filepath),
                "filename": filepath.name,
            }, ensure_ascii=False),
        )
    ]


async def main():
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
