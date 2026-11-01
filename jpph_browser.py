
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent

PROFILE_DIR = BASE_DIR / "browser_profile"

LOGIN_URL = "https://myjpph.jpph.gov.my/login"


async def main():

    async with async_playwright() as p:

        print("Starting Microsoft Edge...")

        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            channel="msedge",
            headless=False
        )

        page = (
            context.pages[0]
            if context.pages
            else await context.new_page()
        )

        print("Opening JPPH login page...")

        await page.goto(
            LOGIN_URL,
            wait_until="domcontentloaded"
        )

        print("\nPlease log in manually to JPPH.")
        print("Do not enter your credentials into this program.")

        input(
            "\nPress ENTER after successful login..."
        )

        print("\nCurrent browser page:")
        print("Title:", await page.title())

        print(
            "Authenticated browser session is ready."
        )

        print(
            "\nNavigate to the document search page "
            "using the JPPH website."
        )

        input(
            "\nPress ENTER after opening the document "
            "search page..."
        )

        print("\nBrowser is ready for the next stage.")

        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
