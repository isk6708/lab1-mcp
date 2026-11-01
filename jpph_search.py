
import asyncio
import re
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

BASE_DIR = Path(__file__).resolve().parent
PROFILE_DIR = BASE_DIR / "browser_profile"

BASE_URL = "https://myjpph.jpph.gov.my"
LOGIN_URL = f"{BASE_URL}/login"
SEARCH_URL = f"{BASE_URL}/search-document-custom/0"


async def extract_results(page):
    """Extract visible document metadata from JPPH search results."""

    data = await page.evaluate("""() => {
        const bodyText = document.body.innerText || "";

        const countMatch = bodyText.match(
            /([0-9,]+)\\s+rekod ditemui/i
        );

        const total = countMatch
            ? parseInt(countMatch[1].replace(/,/g, ""), 10)
            : null;

        const titleLinks = [
            ...document.querySelectorAll(
                'a[href*="/search-document-template/"]'
            )
        ];

        const documents = [];

        for (const titleLink of titleLinks) {

            let current = titleLink;
            let resultContainer = null;
            let downloadLink = null;

            // Find the smallest ancestor containing the title,
            // PDF link and a date.
            for (let i = 0; i < 8 && current; i++) {

                const links = [
                    ...current.querySelectorAll(
                        'a[href*="/searticles-download-solr/"]'
                    )
                ];

                const text = current.innerText || "";

                const dateMatch = text.match(
                    /\\b\\d{2}-\\d{2}-\\d{4}(?:\\s+\\d{2}:\\d{2})?\\b/
                );

                if (links.length > 0 && dateMatch) {
                    resultContainer = current;
                    downloadLink = links[0];
                    break;
                }

                current = current.parentElement;
            }

            if (!resultContainer || !downloadLink) {
                continue;
            }

            const title = titleLink.innerText.trim();
            const filenameText = downloadLink.innerText.trim();

            const filenameParts = filenameText.split("|");

            const filename = filenameParts[0].trim();
            const category = filenameParts.length > 1
                ? filenameParts.slice(1).join("|").trim()
                : "";

            const rowText = resultContainer.innerText || "";

            const dateMatch = rowText.match(
                /\\b\\d{2}-\\d{2}-\\d{4}(?:\\s+\\d{2}:\\d{2})?\\b/
            );

            const titlePath = new URL(
                titleLink.href
            ).pathname;

            const downloadPath = new URL(
                downloadLink.href
            ).pathname;

            documents.push({
                title: title,
                filename: filename,
                category: category,
                date: dateMatch ? dateMatch[0] : null,
                document_path: titlePath,
                download_path: downloadPath
            });
        }

        return {
            total_results: total,
            documents: documents
        };
    }""")

    return data


async def search_documents(query):

    async with async_playwright() as p:

        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            channel="msedge",
            headless=False
        )
        try:
            page = (
                context.pages[0]
                if context.pages
                else await context.new_page()
            )

            await page.goto(
                LOGIN_URL,
                wait_until="domcontentloaded"
            )

            # Allow manual login if the saved session has expired.
            try:
                await page.locator(
                    'input[name="search_criteria"]'
                ).wait_for(timeout=3000)

            except PlaywrightTimeoutError:

                print("Please log in to JPPH manually.")
                input("Press ENTER after successful login...")

            await page.goto(
                SEARCH_URL,
                wait_until="domcontentloaded"
            )

            search_field = page.locator(
                'input[name="search_criteria"]'
            )

            await search_field.wait_for(timeout=15000)

            await search_field.fill(query)
            await search_field.press("Enter")

            # Wait for the search results to render.
            await page.wait_for_timeout(2000)

            try:
                await page.locator(
                    'a[href*="/search-document-template/"]'
                ).first.wait_for(timeout=15000)

            except PlaywrightTimeoutError:
                pass

            results = await extract_results(page)

            return {
                "status": "success",
                "query": query,
                "total_results": results["total_results"],
                "extracted_results": len(results["documents"]),
                "documents": results["documents"]
            }

        finally:
            await context.close()


async def main():

    query = input("Enter JPPH search keyword: ").strip()

    if not query:
        print("Please enter a search keyword.")
        return

    result = await search_documents(query)

    import json

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
