
import os
import sys

from dotenv import load_dotenv
from pypdf import PdfReader
from mcp.server.mcpserver import MCPServer


# --------------------------------------------------
# 1. Load configuration
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))

TARGET_PDF_PATH = os.getenv("TARGET_PDF_PATH", "").strip()


# --------------------------------------------------
# 2. Initialise MCP Server
# --------------------------------------------------

mcp = MCPServer("Llama-PDF-Reader")


# --------------------------------------------------
# 3. Validate PDF file
# --------------------------------------------------

def get_pdf_reader():

    if not TARGET_PDF_PATH:
        raise ValueError(
            "TARGET_PDF_PATH is not configured in .env."
        )

    if not os.path.isfile(TARGET_PDF_PATH):
        raise FileNotFoundError(
            f"PDF file not found: {TARGET_PDF_PATH}"
        )

    return PdfReader(TARGET_PDF_PATH)


# --------------------------------------------------
# 4. MCP Tool: Search PDF
# --------------------------------------------------

@mcp.tool()
def search_pdf_by_keyword(keyword: str) -> str:
    """
    Search the PDF document using a keyword or phrase.

    Returns matching page numbers and relevant text snippets.
    """

    print(
        f"[PDF SEARCH] Searching for: {keyword}",
        file=sys.stderr
    )

    if not keyword or not keyword.strip():
        return "[INVALID_INPUT] Please provide a search keyword."

    try:

        reader = get_pdf_reader()

        search_term = keyword.strip().lower()

        matches = []

        for page_index, page in enumerate(reader.pages):

            page_text = page.extract_text() or ""

            if search_term in page_text.lower():

                lines = page_text.splitlines()

                relevant_lines = [
                    line.strip()
                    for line in lines
                    if search_term in line.lower()
                ]

                matches.append({
                    "page": page_index + 1,
                    "snippets": relevant_lines[:5]
                })

                if len(matches) >= 10:
                    break

        if not matches:

            return (
                f"[PDF_EMPTY] No matches found for "
                f"'{keyword}'. Try alternative keywords."
            )

        result = [
            f"[PDF_SEARCH_SUCCESS]",
            f"Search keyword: {keyword}",
            f"Matching sections: {len(matches)}",
            ""
        ]

        for match in matches:

            result.append(
                f"--- PAGE {match['page']} ---"
            )

            for snippet in match["snippets"]:
                result.append(f"  > {snippet}")

            result.append("")

        if len(matches) >= 10:

            result.append(
                "[NOTE] Results are limited to 10 matching pages. "
                "Try a more specific keyword if necessary."
            )

        return "\n".join(result)

    except Exception as error:

        print(
            f"[PDF SEARCH ERROR] {type(error).__name__}: {error}",
            file=sys.stderr
        )

        return (
            "[PDF_ERROR] Unable to search the PDF document."
        )


# --------------------------------------------------
# 5. MCP Tool: Read PDF Page
# --------------------------------------------------

@mcp.tool()
def read_pdf_page(page_number: int) -> str:
    """
    Read the complete extractable text from a specific PDF page.

    Page numbers start from 1.
    """

    print(
        f"[PDF READ] Reading page: {page_number}",
        file=sys.stderr
    )

    try:

        reader = get_pdf_reader()

        total_pages = len(reader.pages)

        if page_number < 1 or page_number > total_pages:

            return (
                f"[INVALID_PAGE] Valid page range: "
                f"1 to {total_pages}."
            )

        page_text = (
            reader.pages[page_number - 1].extract_text() or ""
        )

        if not page_text.strip():

            return (
                f"[PDF_EMPTY] No extractable text found "
                f"on page {page_number}."
            )

        # Limit returned content to avoid excessively large
        # tool responses.
        max_characters = 6000

        if len(page_text) > max_characters:

            page_text = (
                page_text[:max_characters]
                + "\n\n[NOTE] Page text truncated."
            )

        return (
            "[PDF_PAGE_SUCCESS]\n"
            f"Document page: {page_number}\n"
            f"Total document pages: {total_pages}\n\n"
            f"{page_text}"
        )

    except Exception as error:

        print(
            f"[PDF READ ERROR] {type(error).__name__}: {error}",
            file=sys.stderr
        )

        return (
            "[PDF_ERROR] Unable to read the requested page."
        )


# --------------------------------------------------
# 6. Start MCP Server
# --------------------------------------------------

if __name__ == "__main__":

    print(
        "[MCP] Llama PDF MCP Server starting...",
        file=sys.stderr
    )

    mcp.run()
