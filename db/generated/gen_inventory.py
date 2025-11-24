import csv
import sys
import random

def gen_inventory(num_entries, num_users, num_products):
    filename = 'Inventory.csv'
    fieldnames = ['seller_id', 'product_id', 'quantity']

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for _ in range(num_entries):
            seller_id = random.randint(1, num_users)
            product_id = random.randint(1, num_products)
            quantity = random.randint(1, 100)

            writer.writerow({
                'seller_id': seller_id,
                'product_id': product_id,
                'quantity': quantity
            })

    print(f"{num_entries} inventory records written to {filename}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python gen_inventory.py <num_entries> <num_users> <num_products>")
        sys.exit(1)

    num_entries = int(sys.argv[1])
    num_users = int(sys.argv[2])
    num_products = int(sys.argv[3])
    gen_inventory(num_entries, num_users, num_products)
