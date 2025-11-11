import json
import requests
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

BASE_URL = "https://filmplus.crabdance.com/preview/?q="
INPUT_DIR = "q-generated"
OUTPUT_DIR = "q-success"
TIMEOUT = 10  
MAX_WORKERS = 20  

os.makedirs(OUTPUT_DIR, exist_ok=True)

def check_q(q):
    url = BASE_URL + q
    try:
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") is True:
                return {"q": q, "status": "active"}
        return None
    except Exception as e:
        return None

def main():
    if len(sys.argv) != 2:
        print("َUsage: python3 q-checker.py <Number>")
        sys.exit(1)

    file_number = sys.argv[1]
    input_file = os.path.join(INPUT_DIR, f"q-generated-{file_number}.json")
    output_file = os.path.join(OUTPUT_DIR, f"q-success-{file_number}.json")

    if not os.path.exists(input_file):
        print(f"ERROR: File {input_file} Not Found!")
        sys.exit(1)

    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        params = json.load(f)

    total = len(params)
    print(f"Params: {total:,}")
    print(f"Starting with {MAX_WORKERS} Threads..")

    success_items = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_q = {executor.submit(check_q, item["q"]): item["q"] for item in params}
        for i, future in enumerate(as_completed(future_to_q), 1):
            result = future.result()
            if result:
                success_items.append(result)

            if i % 1000 == 0 or i == total:
                elapsed = time.time() - start_time
                speed = i / elapsed if elapsed > 0 else 0
                print(f"Progress: {i:,}/{total:,} | Speed: {speed:.1f} req/s | Success: {len(success_items)}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(success_items, f, ensure_ascii=False, indent=2)

    duration = time.time() - start_time
    print(f"\Done")
    print(f"Output: {output_file}")
    print(f"Success Count: {len(success_items):,}")
    print(f"Time: {duration:.1f} s")
    print(f"Avg Speed {total/duration:.1f} Req/s")

if __name__ == "__main__":
    main()