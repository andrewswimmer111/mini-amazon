import csv
import requests
import random
import sys
from faker import Faker

# -----------------------------
# CONFIG
# -----------------------------

OUTPUT_FILE = "db/generated/Products.csv"
MAX_CATS = 1500
SAYINGS = ["meow", "hello", "goodbye", "prr"]

fake = Faker()

# -----------------------------
# FETCH CATS (with stable IDs)
# -----------------------------

print("Fetching cats from CATAAS (this may take a few seconds)...")

try:
    cats = requests.get(f"https://cataas.com/api/cats?limit={MAX_CATS}").json()
except Exception as e:
    print("Failed to fetch cats:", e)
    sys.exit(1)

if not isinstance(cats, list):
    print("Unexpected response format:", cats)
    sys.exit(1)

print(f"Retrieved {len(cats)} cats.\n")

# -----------------------------
# CSV SETUP
# -----------------------------

csv_file = open(OUTPUT_FILE, "w", newline="", encoding="utf-8")
writer = csv.writer(csv_file)
writer.writerow(["id", "name", "description", "category"])

# -----------------------------
# GENERATE PRODUCT ROWS
# -----------------------------

cat_id = 1

for cat in cats:
    if cat_id > MAX_CATS:
        break

    # Check malform
    acceptable = ["image/jpeg", "image/png", "image/jpg"]

    image_id = cat.get("id")
    image_type = cat.get("mimetype")
    if not image_id:
        continue  # skip malformed records
    if image_type not in acceptable:
        continue


    # Take the first tag (or fallback)
    tags = cat.get("tags", [])
    first_tag = tags[0] if tags else "unknown"

    parts = first_tag.split()
    if parts and parts[-1] == "cat":
        first_tag = " ".join(parts[:-1])

    # Generate product fields
    name = fake.first_name()
    product = first_tag + " " + name
    saying = random.choice(SAYINGS)
    description = f"{first_tag} cat saying {saying} named {name}"

    writer.writerow([
        cat_id,
        product,
        description,
        saying  # category
    ])

    cat_id += 1

csv_file.close()

print(f"Done! Generated {cat_id-1} cat products into {OUTPUT_FILE}.")

