import json
import string
from itertools import product
import os

CHARS = string.ascii_lowercase  
Q_LENGTH = 5
TARGET_SIZE_MB = 10
TARGET_SIZE_BYTES = TARGET_SIZE_MB * 1024 * 1024  

BYTES_PER_ITEM = 30
items_per_file = TARGET_SIZE_BYTES // BYTES_PER_ITEM  

OUTPUT_DIR = "q-generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

all_combinations = product(CHARS, repeat=Q_LENGTH)

file_index = 1
current_batch = []
current_size = 0

print(f"Start:'{OUTPUT_DIR}' (Each ≈ {TARGET_SIZE_MB} MB)")

for comb in all_combinations:
    q_value = ''.join(comb)
    item = {"q": q_value, "checked": False}
    item_json = json.dumps(item, ensure_ascii=False) + ",\n"
    item_size = len(item_json.encode('utf-8'))

    current_batch.append(item_json)
    current_size += item_size

    if len(current_batch) >= items_per_file or current_size >= TARGET_SIZE_BYTES:
        content = "[\n" + "".join(current_batch)[:-2] + "\n]\n"  # حذف کاما آخر

        filename = f"q-generated-{file_index}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        actual_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"Saved: {filepath} — {len(current_batch):,} Item — {actual_size_mb:.2f} MB")

        file_index += 1
        current_batch = []
        current_size = 0

if current_batch:
    content = "[\n" + "".join(current_batch)[:-2] + "\n]\n"
    filename = f"q-generated-{file_index}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    actual_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"Saved: {filepath} — {len(current_batch):,} Item — {actual_size_mb:.2f} MB")

print(f"\n Completed: {file_index}")
print(f"Files in :{os.path.abspath(OUTPUT_DIR)}")