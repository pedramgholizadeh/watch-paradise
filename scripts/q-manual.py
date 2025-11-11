#!/usr/bin/env python3
"""
q-manual.py (Version 2.0)

Manual checker for q parameters with improved HTML/JSON detection.

Usage:
    python3 q-manual.py bhbhj

Features:
- Handles both JSON and HTML responses
- Extracts movie details (name, rating, year, summary) if valid
- Saves to manual/generated.json (appends, no duplicates)
- Creates 'manual/' folder if missing
"""

import json
import requests
import os
import sys
import re
from pathlib import Path

# ==================== CONFIGURATION ====================
BASE_URL = "https://filmplus.crabdance.com/preview/?i=1&q="
MANUAL_DIR = "manual"
OUTPUT_FILE = os.path.join(MANUAL_DIR, "generated.json")
TIMEOUT = 10  # seconds
# ======================================================

def check_q_parameter(q_value: str):
    """
    Send GET request and determine if q is valid.
    Supports JSON {"ok": true/false} and HTML movie pages.
    Returns dict with details if valid, None otherwise.
    """
    url = BASE_URL + q_value.strip()
    try:
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code != 200:
            return None

        content = response.text.strip()

        # Check if it's JSON
        try:
            data = json.loads(content)
            if data.get("ok") is True:
                # JSON success (rare, but handle it)
                return {"q": q_value.strip(), "status": "active", "type": "json", "details": data}
            else:
                # JSON failure
                return None
        except json.JSONDecodeError:
            # Not JSON, check if HTML movie page
            if "جزئیات فیلم/سریال" in content and "نام:" in content:
                # Extract details using regex (simple parsing)
                details = {}
                details["name"] = re.search(r'نام:\s*(.+?)(?:\n|$)', content, re.DOTALL).group(1).strip() if re.search(r'نام:\s*(.+?)(?:\n|$)', content, re.DOTALL) else "Unknown"
                details["rating"] = re.search(r'امتیاز:\s*([\d.]+/10)', content).group(1) if re.search(r'امتیاز:\s*([\d.]+/10)', content) else "Unknown"
                details["year"] = re.search(r'سال انتشار:\s*(\d{4})', content).group(1) if re.search(r'سال انتشار:\s*(\d{4})', content) else "Unknown"
                details["summary"] = re.search(r'خلاصه:\s*(.+?)(?=\n\n|$)', content, re.DOTALL).group(1).strip() if re.search(r'خلاصه:\s*(.+?)(?=\n\n|$)', content, re.DOTALL) else "Unknown"
                
                return {
                    "q": q_value.strip(),
                    "status": "active",
                    "type": "html",
                    "details": details
                }
            else:
                return None

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def load_existing_results(filepath: str):
    """
    Load existing generated.json if exists.
    Returns list of dicts or empty list.
    """
    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Corrupted JSON in {filepath}, starting fresh: {e}")
        return []
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []


def save_results(filepath: str, results: list):
    """
    Save results to JSON file with pretty formatting.
    """
    # Sort by q for consistency
    results_sorted = sorted(results, key=lambda x: x["q"])

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results_sorted, f, ensure_ascii=False, indent=2)
    print(f"Updated: {filepath} ({len(results_sorted)} entries)")


def main():
    # Check command-line argument
    if len(sys.argv) != 2:
        print("Usage: python3 q-manual.py <q_parameter>")
        print("Example: python3 q-manual.py bhbhj")
        sys.exit(1)

    q_input = sys.argv[1].strip()
    if len(q_input) != 5 or not q_input.isalnum():
        print("Error: q parameter must be exactly 5 alphanumeric characters.")
        sys.exit(1)

    print(f"Checking q = {q_input} ...")

    # Perform the check
    result = check_q_parameter(q_input)
    if not result:
        print("Failed: Invalid or not found (movie not found)")
        sys.exit(0)

    print("Success: Valid movie link!")
    print(f"Movie: {result['details'].get('name', 'Unknown')}")
    print(f"Rating: {result['details'].get('rating', 'Unknown')}")
    print(f"Year: {result['details'].get('year', 'Unknown')}")

    # Ensure manual directory exists
    os.makedirs(MANUAL_DIR, exist_ok=True)

    # Load existing results
    existing = load_existing_results(OUTPUT_FILE)

    # Check for duplicate
    if any(item["q"] == q_input for item in existing):
        print(f"Already exists in {OUTPUT_FILE}. No changes.")
        sys.exit(0)

    # Append new result
    existing.append(result)

    # Save updated list
    save_results(OUTPUT_FILE, existing)


if __name__ == "__main__":
    main()