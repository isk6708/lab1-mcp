#!/usr/bin/env python3
"""
Course: Building AI Applications Through API and MCP Integration
Day 2 - Module 7: Integrating Business Systems (Production MySQL Node)
"""

import sys
import json
import mysql.connector
from mcp.server.fastmcp import FastMCP

# Initialize the primary FastMCP Server engine
mcp = FastMCP("Production-HR-MySQL-Gateway")

@mcp.tool()
def fetch_staff_dependant_records(staff_info_id: str = "") -> str:
    """
    Queries the live MySQL hr database to retrieve active staff employment profiles, 
    job titles, corporate department assignments, and registered dependent demographics.
    Provide a specific staff_info_id string (e.g., '1229') to filter down to a single person.
    """
    print(f"[MySQL Ingress] Initializing connection to sadahrc database...", file=sys.stderr)
    
    # Configure your exact local database access credentials
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'database': 'sadahrc',
        'user': 'root',
        'password': 'raj1005'  # Insert your local root password if applicable
    }
    
    try:
        # Establish the physical connection socket to the local MySQL port
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True) # Returns rows as accessible dictionaries
        
        # Base production SQL statement mapped exactly from your enterprise layout
        base_query = """
        SELECT 
            c.staff_name, c.staff_no, c.staff_ic, e.job_title, g.company_name,
            a.dependant_name, a.dependant_ic, 
            DATE_FORMAT(a.dependant_dob,'%d/%m/%Y') AS tarikh_lahir, 
            b.descr AS relationship_desc 
        FROM `hr_dependant_info` a 
        INNER JOIN sys_ref b ON b.code = a.dependant_rel 
        INNER JOIN hr_staff_info c ON c.id = a.staff_info_id
        INNER JOIN hr_employment_info d ON d.staff_info_id = c.id
        INNER JOIN hr_job_ref e ON e.id = d.job_id
        INNER JOIN hr_company_info f ON f.id = e.company_id
        INNER JOIN hr_company_info g ON g.id = f.dept_id
        WHERE d.engagement_active = '1' AND b.cat = 'RELCD'
        """
        
        # Dynamically append the filtration parameter array if specified by the AI agent intent
        if staff_info_id.strip():
            base_query += f" AND a.`staff_info_id` = '{staff_info_id.strip()}'"
            
        base_query += " ORDER BY c.id, b.sort;"
        
        print(f"[MySQL Executing]: {base_query[:120]}...", file=sys.stderr)
        cursor.execute(base_query)
        rows = cursor.fetchall()
        
        # Close connection pipelines cleanly
        cursor.close()
        connection.close()
        
        if not rows:
            return f"[SQL_EMPTY] Transaction finalized. 0 records located matching criteria (Staff ID: {staff_info_id or 'ALL'})."
            
        # Compile records into a clean, human-scannable structural layout text block for the LLM context
        output_buffer = [f"=== HR DATABASE EXTRACTION SUCCESS ({len(rows)} ROWS RETURNED) ==="]
        for idx, row in enumerate(rows, 1):
            output_buffer.append(
                f"Record #{idx}:\n"
                f"  Staff  : {row['staff_name']} ({row['staff_no']}) | IC: {row['staff_ic']}\n"
                f"  Designation: {row['job_title']} at {row['company_name']}\n"
                f"  Dependent: {row['dependant_name']} ({row['relationship_desc']}) | IC: {row['dependant_ic']} | DOB: {row['tarikh_lahir']}"
            )
            
        return "\n".join(output_buffer)
        
    except mysql.connector.Error as err:
        print(f"[MySQL Exception]: Database transaction crash: {err}", file=sys.stderr)
        return f"[SQL_ERROR] Failed to query local MySQL instance. Database Driver Reason: {err}"

if __name__ == "__main__":
    mcp.run()
