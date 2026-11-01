
#!/usr/bin/env python3
"""
Course: Building AI Applications Through API and MCP Integration
Day 2 - Module 7: Integrating Business Systems
Component: Production HR MySQL MCP Server
"""

import os
import sys
import mysql.connector

from dotenv import load_dotenv
# from mcp.server.fastmcp import FastMCP
from mcp.server.mcpserver import MCPServer

# Load environment variables
load_dotenv()

# Initialize the MCP Server
# mcp = FastMCP("Production-HR-MySQL-Gateway")
mcp = MCPServer("Production-HR-MySQL-Gateway")


@mcp.tool()

@mcp.tool()
def fetch_staff_dependant_records(
    search_term: str = "",
    staff_info_id: str = ""
) -> str:
    """
    Search active HR staff and dependent records.

    Searchable fields:
    - Staff name
    - Dependent name
    - Staff number

    Optional filter:
    - Staff information ID

    Example:
    search_term = "Ahmad"
    search_term = "STF001"
    staff_info_id = "1229"

    At least one search parameter must be provided.
    """

    print(
        "[MySQL Ingress] Searching HR database...",
        file=sys.stderr
    )

    db_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "database": os.getenv("DB_NAME", "sadahrc"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD")
    }

    connection = None
    cursor = None

    try:

        # Validate database credentials
        if not db_config["user"] or not db_config["password"]:
            return "[SQL_ERROR] Database credentials are not configured."

        # Validate search inputs
        search_term = search_term.strip()
        staff_info_id = staff_info_id.strip()

        if not search_term and not staff_info_id:
            return (
                "[INPUT_REQUIRED] Please provide a staff name, "
                "dependent name, staff number, or staff information ID."
            )

        if staff_info_id and not staff_info_id.isdigit():
            return "[SQL_ERROR] Staff ID must contain digits only."

        if len(search_term) > 100:
            return "[SQL_ERROR] Search term is too long."

        # Establish MySQL connection
        connection = mysql.connector.connect(**db_config)

        cursor = connection.cursor(dictionary=True)

        # Base SQL query
        base_query = """
            SELECT
                c.id AS staff_info_id,
                c.staff_name,
                c.staff_no,
                e.job_title,
                g.company_name,
                a.dependant_name,
                b.descr AS relationship_desc

            FROM hr_dependant_info a

            INNER JOIN sys_ref b
                ON b.code = a.dependant_rel

            INNER JOIN hr_staff_info c
                ON c.id = a.staff_info_id

            INNER JOIN hr_employment_info d
                ON d.staff_info_id = c.id

            INNER JOIN hr_job_ref e
                ON e.id = d.job_id

            INNER JOIN hr_company_info f
                ON f.id = e.company_id

            INNER JOIN hr_company_info g
                ON g.id = f.dept_id

            WHERE d.engagement_active = '1'
              AND b.cat = 'RELCD'
        """

        query_parameters = []

        # Search across staff name, dependent name and staff number
        if search_term:

            base_query += """
                AND (
                    c.staff_name LIKE %s
                    OR a.dependant_name LIKE %s
                    OR c.staff_no LIKE %s
                )
            """

            search_pattern = f"%{search_term}%"

            query_parameters.extend([
                search_pattern,
                search_pattern,
                search_pattern
            ])

        # Optional staff information ID filter
        if staff_info_id:

            base_query += " AND a.staff_info_id = %s"

            query_parameters.append(staff_info_id)

        # Limit the number of returned records
        base_query += """
            ORDER BY c.id, b.sort
            LIMIT 50
        """

        print(
            "[MySQL Executing] HR staff and dependent search...",
            file=sys.stderr
        )

        cursor.execute(
            base_query,
            tuple(query_parameters)
        )

        rows = cursor.fetchall()

        if not rows:

            return (
                "[SQL_EMPTY] No matching HR records found. "
                f"Search term: {search_term or 'N/A'}"
            )

        # Format database results
        output_buffer = [
            f"=== HR SEARCH SUCCESS ({len(rows)} ROWS RETURNED) ==="
        ]

        for idx, row in enumerate(rows, 1):

            output_buffer.append(
                f"Record #{idx}:\n"
                f"  Staff ID: {row['staff_info_id']}\n"
                f"  Staff Name: {row['staff_name']}\n"
                f"  Staff Number: {row['staff_no']}\n"
                f"  Designation: {row['job_title']}\n"
                f"  Department: {row['company_name']}\n"
                f"  Dependent: {row['dependant_name']}\n"
                f"  Relationship: {row['relationship_desc']}"
            )

        return "\n".join(output_buffer)

    except mysql.connector.Error as err:

        print(
            f"[MySQL Exception] {err}",
            file=sys.stderr
        )

        return "[SQL_ERROR] Unable to retrieve HR records."

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()



if __name__ == "__main__":

    print(
        "[MCP Server] Production HR MySQL Gateway starting...",
        file=sys.stderr
    )

    # stdio transport allows the MCP client to launch this server
    # mcp.run(transport="stdio")
    mcp.run()
