
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent
PROFILE_DIR = BASE_DIR / "browser_profile"

async def main():

    async with async_playwright() as p:

        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            channel="msedge",
            headless=False
        )

        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(
            "https://myjpph.jpph.gov.my/login",
            wait_until="domcontentloaded"
        )

        print("Please log in to JPPH manually.")
        print("After login, confirm that the dashboard is displayed.")

        input("Press ENTER after successful login...")

        print("Closing browser and saving the browser session.")

        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
