
import asyncio
from pathlib import Path
import sys

from mcp.server.mcpserver import MCPServer
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# BASE_DIR = Path(__file__).resolve().parent.parent
# PROFILE_DIR = BASE_DIR / "browser_profile"
# PROFILE_DIR = Path(__file__).resolve().parent / "browser_profile"

BASE_DIR = Path(__file__).resolve().parent
PROFILE_DIR = BASE_DIR / "browser_profile"

LOGIN_URL = "https://myjpph.jpph.gov.my/login"
BASE_URL = "https://myjpph.jpph.gov.my"
SEARCH_URL = f"{BASE_URL}/search-document-custom/0"
mcp = MCPServer("jpph-document-search")



async def perform_search(query: str):

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

            print(
                f"Using profile: {PROFILE_DIR}",
                file=sys.stderr,
                flush=True
            )

            # Open the login page first.
            await page.goto(
                LOGIN_URL,
                wait_until="domcontentloaded"
            )

            # Check whether the user is already authenticated.
            search_field = page.locator(
                'input[name="search_criteria"]'
            )

            try:
                await search_field.wait_for(timeout=3000)

            except PlaywrightTimeoutError:

                print(
                    "JPPH login may be required. "
                    "Please log in manually in the Edge window.",
                    file=sys.stderr,
                    flush=True
                )

                # Wait for manual authentication.
                # No credentials are collected by this program.
                try:
                    await page.wait_for_url(
                        lambda url: "/login" not in str(url).lower(),
                        timeout=120000
                    )

                    await page.locator(
                        'input[name="search_criteria"]'
                    ).wait_for(timeout=30000)

                except PlaywrightTimeoutError:

                    return {
                        "status": "authentication_required",
                        "message": (
                            "JPPH authentication was not completed. "
                            "Please log in manually and try again."
                        ),
                        "current_url": page.url
                    }

            # Navigate to the clean search page.
            await page.goto(
                SEARCH_URL,
                wait_until="domcontentloaded"
            )

            print(
                f"Search page URL: {page.url}",
                file=sys.stderr,
                flush=True
            )

            search_field = page.locator(
                'input[name="search_criteria"]'
            )

            try:
                await search_field.wait_for(timeout=15000)

            except PlaywrightTimeoutError:

                return {
                    "status": "authentication_required",
                    "message": (
                        "The JPPH search field is unavailable. "
                        "Please check your login session."
                    ),
                    "current_url": page.url
                }

            await search_field.fill(query)
            await search_field.press("Enter")

            # Allow results to render.
            await page.wait_for_timeout(2000)

            try:
                await page.locator(
                    'a[href*="/search-document-template/"]'
                ).first.wait_for(timeout=15000)

            except PlaywrightTimeoutError:
                # Zero results may be a valid search outcome.
                pass

            result = await page.evaluate("""() => {

                const text = document.body.innerText || "";

                const match = text.match(
                    /([0-9,]+)\\s+rekod ditemui/i
                );

                const total = match
                    ? parseInt(match[1].replace(/,/g, ""), 10)
                    : null;

                const links = [
                    ...document.querySelectorAll(
                        'a[href*="/search-document-template/"]'
                    )
                ];

                const documents = [];

                for (const titleLink of links) {

                    let node = titleLink;
                    let container = null;
                    let downloadLink = null;

                    for (let i = 0; i < 8 && node; i++) {

                        const downloads = [
                            ...node.querySelectorAll(
                                'a[href*="/searticles-download-solr/"]'
                            )
                        ];

                        const rowText = node.innerText || "";

                        const dateMatch = rowText.match(
                            /\\b\\d{2}-\\d{2}-\\d{4}(?:\\s+\\d{2}:\\d{2})?\\b/
                        );

                        if (downloads.length && dateMatch) {
                            container = node;
                            downloadLink = downloads[0];
                            break;
                        }

                        node = node.parentElement;
                    }

                    if (!container || !downloadLink) continue;

                    const rowText = container.innerText || "";

                    const dateMatch = rowText.match(
                        /\\b\\d{2}-\\d{2}-\\d{4}(?:\\s+\\d{2}:\\d{2})?\\b/
                    );

                    const filenameParts =
                        downloadLink.innerText.trim().split("|");

                    documents.push({
                        title: titleLink.innerText.trim(),
                        filename: filenameParts[0].trim(),
                        category: filenameParts.length > 1
                            ? filenameParts.slice(1).join("|").trim()
                            : null,
                        date: dateMatch ? dateMatch[0] : null,
                        document_path: new URL(titleLink.href).pathname,
                        download_path: new URL(downloadLink.href).pathname
                    });
                }

                return {
                    total_results: total,
                    documents: documents
                };
            }""")

            print(
                "Current search URL:",
                page.url,
                file=sys.stderr,
                flush=True
            )

            print(
                "Page text:",
                (await page.locator("body").inner_text())[:3000],
                file=sys.stderr,
                flush=True
            )
            return {
                "status": "success",
                "query": query,
                "total_results": result["total_results"],
                "extracted_results": len(result["documents"]),
                "documents": result["documents"]
            }

        finally:
            await context.close()
 
  
@mcp.tool()
async def search_documents(query: str) -> dict:
      """
      Search the authenticated JPPH document-search application.
  
      Returns matching document titles, filenames, categories and dates.
      Read-only operation.
      """
  
      if not query or not query.strip():
          return {
              "status": "error",
              "message": "Search keyword cannot be empty."
          }
  
      return await perform_search(query.strip())

async def inspect_jpph_page():

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

            print(
                "JPPH opened. Log in manually if required.",
                flush=True
            )

            # Allow time for manual authentication.
            # Do not enter credentials through this program.
            await page.wait_for_timeout(30000)

            current_path = await page.evaluate(
                "() => window.location.pathname"
            )

            if current_path == "/login":
                return {
                    "status": "login_required",
                    "message": "Please log in to JPPH manually."
                }

            page_text = await page.locator("body").inner_text()

            return {
                "status": "success",
                "page_title": await page.title(),
                "page_path": current_path,
                "visible_content": page_text[:12000]
            }

        finally:
            await context.close()


@mcp.tool()
async def inspect_jpph() -> dict:
    """
    Inspect the currently accessible JPPH page.
    Returns visible page text for development and testing.
    """

    return await inspect_jpph_page()


if __name__ == "__main__":
    mcp.run()
