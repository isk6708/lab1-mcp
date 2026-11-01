#!/usr/bin/env python3
"""
Course: Building AI Applications Through API and MCP Integration
Day 2 - Module 7: Integrating Business Systems (Production PDF File Scanner)
"""

import sys
import os
from pypdf import PdfReader
# from mcp.server.fastmcp import FastMCP
from mcp.server.mcpserver import MCPServer

# Initialize the PDF parsing server instance
mcp = MCPServer("Production-PDF-Reader")

# Explicit file configuration target matching your local path parameters
TARGET_PDF_PATH = r"C:\RajWork\2026\ESLearning\github\9781835468944.pdf"

@mcp.tool()
def search_pdf_by_keyword(keyword: str) -> str:
    """
    Opens and scans the local enterprise Packt Publishing textbook PDF file.
    Searches every page dynamically for matches against the provided keyword argument string,
    returning text snippet contexts along with the target page numbers.
    """
    print(f"[PDF Ingress] Validating file accessibility for path: {TARGET_PDF_PATH}", file=sys.stderr)
    
    if not os.path.exists(TARGET_PDF_PATH):
        return f"[FILE_NOT_FOUND] Critical: Unable to locate target file asset at system path: {TARGET_PDF_PATH}"
        
    try:
        # Initialize binary layout parsing sequence via pypdf
        reader = PdfReader(TARGET_PDF_PATH)
        total_pages = len(reader.pages)
        print(f"[PDF Status] Ingesting {total_pages} total document pages...", file=sys.stderr)
        
        matches = []
        search_term = keyword.strip().lower()
        
        # Scan pages dynamically
        for page_num in range(total_pages):
            page_text = reader.pages[page_num].extract_text()
            if page_text and search_term in page_text.lower():
                # Extract surrounding snippet context to keep token load efficient
                lines = page_text.split('\n')
                relevant_lines = [line.strip() for line in lines if search_term in line.lower()]
                
                matches.append(
                    f"--- PAGE {page_num + 1} MATCHES ---\n"
                    f"Context Snippets:\n" + "\n".join(f"  > {l}" for l in relevant_lines[:3])
                )
                
                # Safeguard limits to prevent overflowing the LLM context frame
                if len(matches) >= 10:
                    matches.append("... [TRUNCATED] Extra occurrences found. Refine your keyword search phrase.")
                    break
                    
        if matches:
            return f"[PDF_MATCH_SUCCESS] Keyword '{keyword}' located across {len(matches)} sections:\n\n" + "\n".join(matches)
        else:
            return f"[PDF_EMPTY] Document scan completed. 0 occurrences found matching query term: '{keyword}'."
            
    except Exception as e:
        print(f"[PDF Exception] Layout parsing failure: {e}", file=sys.stderr)
        return f"[PDF_ERROR] System failed to safely read document structure. Reason: {e}"

if __name__ == "__main__":
    mcp.run()
