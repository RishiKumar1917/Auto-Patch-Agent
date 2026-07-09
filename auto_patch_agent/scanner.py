import re

def scan_code(file_content):
    """
    Scans Python code for common security vulnerabilities.
    Returns a list of vulnerability dictionaries.
    """
    vulnerabilities = []
    lines = file_content.split("\n")

    # check for sql injection (string formating inside execute)
    sql_injection_pattern = re.compile(r"\.execute\s*\(\s*f[\"'].*\{.*\}[\"']\s*\)")
    sql_injection_pattern_alternative = re.compile(r"\.execute\s*\(\s*[\"'].*[\"']\s*%\s*\(?.*\)?\s*\)")
    
    # check for hardcoded passwords and api keys
    secret_pattern = re.compile(r"(password|api_key|secret|token)\s*=\s*[\"']([^\"']{8,})[\"']", re.IGNORECASE)

    for i, line in enumerate(lines):
        line_number = i + 1
        
        # check if it matches sql injection pattern
        if sql_injection_pattern.search(line) or sql_injection_pattern_alternative.search(line) or ("SELECT" in line and "f\"" in line and ".execute" in lines[min(i+1, len(lines)-1)]):
            vulnerabilities.append({
                "id": "SQL-INJECTION",
                "line": line_number,
                "code": line.strip(),
                "severity": "CRITICAL",
                "description": "SQL Injection vulnerability: User input is directly formatted into a SQL query. Use parameterized queries instead.",
                "remediation": "Replace string interpolation with query parameters (e.g., cursor.execute('SELECT * FROM users WHERE username = ?', (username,)))"
            })
            
        # check if it has hardcoded passwords or secrets
        secret_match = secret_pattern.search(line)
        if secret_match:
            # skip if it is just a variable assign and not a string
            value = secret_match.group(2)
            if "admin" in line.lower() or len(value) > 10:
                vulnerabilities.append({
                    "id": "HARDCODED-SECRET",
                    "line": line_number,
                    "code": line.strip(),
                    "severity": "HIGH",
                    "description": f"Hardcoded credential/secret detected for '{secret_match.group(1)}'. Storing plain-text secrets in code is highly insecure.",
                    "remediation": "Retrieve credentials from environment variables or a secure secret manager (e.g., os.environ.get('ADMIN_PASSWORD'))."
                })

    return vulnerabilities
