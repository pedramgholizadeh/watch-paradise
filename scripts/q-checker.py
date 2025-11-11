#!/usr/bin/env python3
"""
q-checker.py

Batch checker for q parameters from q-generated-N.json files.
Saves only valid q values with movie details to q-success/q-success-N.json

Usage:
    python3 q-checker.py 1
"""

import json
import requests
import os
import sys
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== CONFIGURATION ====================
BASE_URL = "https://filmplus.crabdance.com/preview/?i=1&q="  # i=1 is required
INPUT_DIR = "q-generated"
OUTPUT_DIR = "q-success"
TIMEOUT = 10                  # Request timeout in seconds
MAX_WORKERS = 100             # Adjust based on server tolerance (50–100 safe)
# ======================================================

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)


def is_valid_html_page(html_content: str) -> bool:
    """
    Check if HTML contains signs of a valid movie/series detail page.
    Looks for Persian keywords like "جزئیات فیلم/سریال" and "نام:"
    """
    return "جزئیات فیلم/سریال" in html_content and "نام:" in html_content


def extract_movie_details(html_content: str) -> dict:
    """
    Extract movie/series metadata from HTML using regex.
    Returns dict with name, rating, year, summary.
    """
    details = {}

    # Name
    name_match = re.search(r'نام:\s*<[^>]*>([^<]+)<', html_content)
    if name_match:
        details["name"] = name_match.group(1).strip()
    else:
        details["name"] = "Unknown"

    # Rating
    rating_match = re.search(r'امتیاز:\s*<[^>]*>([\d.]+/10)<', html_content)
    if rating_match:
        details["rating"] = rating_match.group(1).strip()
    else:
        details["rating"] = "Unknown"

    # Year
    year_match = re.search(r'سال انتشار:\s*<[^>]*>(\d{4})<', html_content)
    if year_match:
        details["year"] = year_match.group(1).strip()
    else:
        details["year"] = "Unknown"

    # Summary (first paragraph after "خلاصه:")
    summary_match = re.search(r'خلاصه:\s*<[^>]*>(.+?)</', html_content, re.DOTALL)
    if summary_match:
        summary = summary_match.group(1)
        # Clean up HTML tags and whitespace
        summary = re.sub(r'<[^>]+>', '', summary)
        summary = re.sub(r'\s+', ' ', summary).strip()
        details["summary"] = summary[:500] + "..." if len(summary) > 500 else summary
    else:
        details["summary"] = "No summary available"

    return details


def check_q(q_value: str):
    """
    Check a single q parameter.
    Returns dict with q, status, and details if valid; None otherwise.
    """
    url = BASE_URL + q_value
    try:
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code != 200:
            return None

        content = response.text.strip()

        # Try JSON first
        try:
            data = json.loads(content)
            if data.get("ok") is True:
                return {
                    "q": q_value,
                    "status": "active",
                    "type": "json",
                    "details": data
                }
            else:
                return None
        except json.JSONDecodeError:
            # Not JSON → must be HTML
            if is_valid_html_page(content):
                details = extract_movie_details(content)
                return {
                    "q": q_value,
                    "status": "active",
                    "type": "html",
                    "details": details
                }
            else:
                return None

    except requests.RequestException:
        return None
    except Exception:
        return None


def main():
    # Validate input
    if len(sys.argv) != 2:
        print("Usage: python3 q-checker.py <file_number>")
        print("Example: python3 q-checker.py 1")
        sys.exit(1)

    try:
        file_number = int(sys.argv[1])
    except ValueError:
        print("Error: File number must be an integer.")
        sys.exit(1)

    input_file = os.path.join(INPUT_DIR, f"q-generated-{file_number}.json")
    output_file = os.path.join(OUTPUT_DIR, f"q-success-{file_number}.json")

    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}")
        sys.exit(1)

    # Load parameters
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        try:
            params = json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in {input_file}: {e}")
            sys.exit(1)

    total = len(params)
    if total == 0:
        print("No parameters to check.")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return

    print(f"Total parameters: {total:,}")
    print(f"Starting scan with {MAX_WORKERS} concurrent threads...")

    # Results storage
    success_items = []
    start_time = time.time()

    # Execute in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all jobs
        future_to_q = {
            executor.submit(check_q, item["q"]): item["q"]
            for item in params
        }

        # Collect results
        for i, future in enumerate(as_completed(future_to_q), 1):
            result = future.result()
            if result:
                success_items.append(result)

            # Progress update
            if i % 1000 == 0 or i == total:
                elapsed = time.time() - start_time
                speed = i / elapsed if elapsed > 0 else 0
                print(f"Progress: {i:,}/{total:,} | "
                      f"Speed: {speed:.1f} req/s | "
                      f"Success: {len(success_items):,}")

    # Save only valid results
    success_items_sorted = sorted(success_items, key=lambda x: x["q"])
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(success_items_sorted, f, ensure_ascii=False, indent=2)

    # Final stats
    duration = time.time() - start_time
    avg_speed = total / duration if duration > 0 else 0

    print("\n" + "="*60)
    print("SCAN COMPLETE")
    print("="*60)
    print(f"Output file: {output_file}")
    print(f"Valid q found: {len(success_items):,}")
    print(f"Total time: {duration:.1f} seconds")
    print(f"Average speed: {avg_speed:.1f} requests/second")
    print("="*60)


if __name__ == "__main__":
    main()