import csv
import sys
import random

def gen_ledger(num_entries, num_users, num_products, num_purchases):
    filename = 'Ledger.csv'
    fieldnames = ['purchase_id', 'seller_id', 'product_id', 'quantity', 'fulfillment_status']

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for _ in range(num_entries):
            purchase_id = random.randint(1, num_purchases)
            seller_id = random.randint(1, num_users)
            product_id = random.randint(1, num_products)
            quantity = random.randint(1, 10)
            fulfillment_status = random.randint(0, 1)

            writer.writerow({
                'purchase_id': purchase_id,
                'seller_id': seller_id,
                'product_id': product_id,
                'quantity': quantity,
                'fulfillment_status': fulfillment_status
            })

    print(f"{num_entries} ledger records written to {filename}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python gen_ledger.py <num_entries> <num_users> <num_products> <num_purchases>")
        sys.exit(1)

    num_entries = int(sys.argv[1])
    num_users = int(sys.argv[2])
    num_products = int(sys.argv[3])
    num_purchases = int(sys.argv[4])

    gen_ledger(num_entries, num_users, num_products, num_purchases)
