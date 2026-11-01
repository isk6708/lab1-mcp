
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

        page = (
            context.pages[0]
            if context.pages
            else await context.new_page()
        )

        print("Opening JPPH website...")

        await page.goto(
            "https://myjpph.jpph.gov.my/login",
            wait_until="domcontentloaded"
        )

        print("\nIf necessary, log in manually.")
        print("Navigate to the document search page.")
        print("Perform a search, for example: Tadbir urus.")

        input("\nPress ENTER after search results appear...")

        # Extract visible page text
        page_text = await page.locator("body").inner_text()

        print("\n========== SEARCH PAGE CONTENT ==========")
        print(page_text[:10000])

        # Inspect visible form elements
        print("\n========== FORM ELEMENTS ==========")

        forms = await page.locator("form").count()

        print("Forms found:", forms)

        inputs = await page.locator("input:visible").all()

        for index, element in enumerate(inputs):

            print({
                "index": index,
                "type": await element.get_attribute("type"),
                "name": await element.get_attribute("name"),
                "placeholder": await element.get_attribute("placeholder"),
                "id": await element.get_attribute("id")
            })

        # Inspect visible buttons
        print("\n========== BUTTONS ==========")

        buttons = await page.locator("button:visible").all()

        for index, button in enumerate(buttons):

            print({
                "index": index,
                "text": (await button.inner_text())[:100],
                "type": await button.get_attribute("type")
            })

        # Inspect visible links without exposing query strings
        print("\n========== DOCUMENT LINKS ==========")

        links = await page.locator("a:visible").all()

        for index, link in enumerate(links[:30]):

            print({
                "index": index,
                "text": (await link.inner_text())[:150],
                "path": await link.evaluate(
                    "(el) => el.pathname"
                )
            })

        print("\nInspection completed.")

        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
