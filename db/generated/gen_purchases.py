import csv
import sys
import os
import random
from datetime import datetime, timedelta, timezone
from faker import Faker

LEDGER_FILENAME_DEFAULT = "Ledger.csv"
PURCHASES_FILENAME = "Purchases.csv"

def load_ledger_info(ledger_filename):
    """
    Returns:
      purchase_ids: sorted list of unique purchase_id ints
      status_by_purchase: dict[purchase_id] -> 0/1
        1 if all rows for that purchase_id in ledger have fulfillment_status = 1
        0 if any row has 0
    """
    if not os.path.exists(ledger_filename):
        print(f"Ledger file '{ledger_filename}' not found")
        sys.exit(1)

    status_by_purchase = {}
    purchase_ids_set = set()

    with open(ledger_filename, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = int(row["purchase_id"])
            fs = int(row["fulfillment_status"])
            purchase_ids_set.add(pid)

            if pid not in status_by_purchase:
                status_by_purchase[pid] = 1
            if fs == 0:
                status_by_purchase[pid] = 0

    purchase_ids = sorted(purchase_ids_set)
    return purchase_ids, status_by_purchase

def gen_purchases(num_users, ledger_filename=LEDGER_FILENAME_DEFAULT):
    fake = Faker()
    purchase_ids, status_by_purchase = load_ledger_info(ledger_filename)

    fieldnames = ["purchase_id", "address", "date", "buyer_id", "fulfillment_status"]

    with open(PURCHASES_FILENAME, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for pid in purchase_ids:
            address = fake.address().replace("\n", ", ")

            # random datetime in last 30 days, with timezone
            dt = datetime.now(timezone.utc) - timedelta(
                days=random.randint(0, 30),
                seconds=random.randint(0, 86400),
            )
            date_str = dt.isoformat(sep=" ", timespec="seconds")

            buyer_id = random.randint(1, num_users)
            fulfillment_status = status_by_purchase.get(pid, 0)

            writer.writerow({
                "purchase_id": pid,
                "address": address,
                "date": date_str,
                "buyer_id": buyer_id,
                "fulfillment_status": fulfillment_status,
            })

    print(f"{len(purchase_ids)} purchases written to {PURCHASES_FILENAME}")
    print(f"Derived from {ledger_filename}")

if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print("Usage: python gen_purchases.py <num_users> [ledger_filename]")
        sys.exit(1)

    num_users = int(sys.argv[1])
    if len(sys.argv) == 3:
        ledger_filename = sys.argv[2]
    else:
        ledger_filename = LEDGER_FILENAME_DEFAULT

    gen_purchases(num_users, ledger_filename)
