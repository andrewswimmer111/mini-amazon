import csv
import sys
import random
import hashlib
from faker import Faker
from decimal import Decimal, ROUND_HALF_UP

from werkzeug.security import generate_password_hash

def sha256_encode(password):
    return generate_password_hash(password)

def gen_users(num_users):
    fake = Faker()
    filename = 'Users.csv'
    fieldnames = ['id', 'firstname', 'lastname', 'email', 'password', 'address', 'balance']

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        # Add the required specific user
        writer.writerow({
            'id': 1,
            'firstname': 'Thomas',
            'lastname': 'Lee',
            'email': 'thomas15@yahoo.com',
            'password': sha256_encode('pass0'),
            'address': fake.address().replace('\n', ', '),
            'balance': Decimal(random.uniform(0, 1000)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        })

        # Generate remaining users
        for i in range(2, num_users + 1):
            first = fake.first_name()
            last = fake.last_name()
            email = f"{first.lower()}.{last.lower()}{random.randint(1,99)}@example.com"
            password = sha256_encode(f"pass{i}")
            address = fake.address().replace('\n', ', ')
            balance = Decimal(random.uniform(0, 1000)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

            writer.writerow({
                'id': i,
                'firstname': first,
                'lastname': last,
                'email': email,
                'password': password,
                'address': address,
                'balance': balance
            })

    print(f"{num_users} users written to {filename}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python gen_users.py <num_users>")
        sys.exit(1)

    num_users = int(sys.argv[1])
    gen_users(num_users)
