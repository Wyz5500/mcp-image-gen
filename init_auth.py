"""Open ChatGPT in the dedicated Chrome profile so the user can log in."""

from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE_DIR = Path(__file__).resolve().parent / "chrome-profile"


def main():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.new_page()
        page.goto("https://chatgpt.com/images")

        page.evaluate("() => { window.__escPressed = false }")
        page.evaluate(
            """() => {
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'Escape') { window.__escPressed = true }
                });
            }"""
        )

        print("\n  Log into ChatGPT in the browser, then press ESC to exit.\n")
        import time
        while True:
            if page.evaluate("() => window.__escPressed"):
                break
            time.sleep(0.5)

        page.close()
        context.close()


if __name__ == "__main__":
    main()
