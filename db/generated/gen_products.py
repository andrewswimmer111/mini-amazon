import csv
import sys
import random
from faker import Faker
from decimal import Decimal, ROUND_HALF_UP

def gen_products(num_products):
    fake = Faker()
    filename = 'Products.csv'
    fieldnames = ['id', 'name', 'description', 'price', 'category']

    # Product categories must match database ENUM: 'A', 'B', 'C', 'D'
    categories = ['A', 'B', 'C', 'D']

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(1, num_products + 1):
            name = fake.catch_phrase()
            description = fake.paragraph(nb_sentences=3)
            price = Decimal(random.uniform(5, 1000)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
            category = random.choice(categories)

            writer.writerow({
                'id': i,
                'name': name,
                'description': description,
                'price': price,
                'category': category
            })

    print(f"{num_products} products written to {filename}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python gen_products.py <num_products>")
        sys.exit(1)

    num_products = int(sys.argv[1])
    gen_products(num_products)
