
import os
import sys
from dotenv import load_dotenv
from pypdf import PdfReader
from mcp.server.mcpserver import MCPServer

load_dotenv()

mcp = MCPServer("Production-PDF-Reader")

TARGET_PDF_PATH = os.getenv("TARGET_PDF_PATH", "")


@mcp.tool()
def search_pdf_by_keyword(keyword: str) -> str:
    """
    Search a local PDF document by keyword.
    Returns matching page numbers and short text snippets.
    """

    keyword = keyword.strip()

    if not keyword:
        return "[INVALID_INPUT] Please provide a keyword."

    if len(keyword) > 100:
        return "[INVALID_INPUT] Keyword is too long."

    if not TARGET_PDF_PATH:
        return "[CONFIG_ERROR] TARGET_PDF_PATH is not configured."

    if not os.path.isfile(TARGET_PDF_PATH):
        return "[FILE_NOT_FOUND] The configured PDF file does not exist."

    try:
        reader = PdfReader(TARGET_PDF_PATH)
        matches = []
        search_term = keyword.lower()

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""

            if search_term not in page_text.lower():
                continue

            matching_lines = [
                line.strip()
                for line in page_text.splitlines()
                if search_term in line.lower()
            ]

            snippets = matching_lines[:3]

            # Keep returned text brief.
            snippet_text = "\n".join(snippets)[:500]

            matches.append(
                f"Page {page_number}:\n{snippet_text}"
            )

            if len(matches) >= 10:
                break

        if not matches:
            return (
                f"[PDF_EMPTY] No occurrences of '{keyword}' "
                "were found."
            )

        return (
            f"[PDF_MATCH_SUCCESS] Found matches for '{keyword}' "
            f"in {len(matches)} page(s):\n\n"
            + "\n\n".join(matches)
        )

    except Exception as error:
        print(
            f"[PDF ERROR] {type(error).__name__}: {error}",
            file=sys.stderr
        )
        return "[PDF_ERROR] Unable to read the PDF document."


@mcp.tool()
def read_pdf_page(page_number: int) -> str:
    """
    Retrieve readable text from a specific PDF page.
    Returns a limited amount of text for AI analysis.
    """

    if not TARGET_PDF_PATH:
        return "[CONFIG_ERROR] PDF path is not configured."

    if not os.path.isfile(TARGET_PDF_PATH):
        return "[FILE_NOT_FOUND] PDF document not found."

    try:
        reader = PdfReader(TARGET_PDF_PATH)

        total_pages = len(reader.pages)

        if page_number < 1 or page_number > total_pages:
            return (
                f"[INVALID_PAGE] Valid page range: 1-{total_pages}"
            )

        page_text = (
            reader.pages[page_number - 1].extract_text() or ""
        )

        if not page_text.strip():
            return (
                f"[PDF_EMPTY] No extractable text on page "
                f"{page_number}."
            )

        return (
            f"[PDF_PAGE_SUCCESS]\n"
            f"Page: {page_number}\n\n"
            f"{page_text[:2500]}"
        )

    except Exception as error:

        print(
            f"[PDF ERROR] {type(error).__name__}: {error}",
            file=sys.stderr
        )

        return "[PDF_ERROR] Unable to read the requested page."

if __name__ == "__main__":
    mcp.run()
