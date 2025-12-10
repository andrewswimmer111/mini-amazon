# gen_data.py

from werkzeug.security import generate_password_hash

import csv
import random
from faker import Faker
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from gen_cat_products import gen_cat_products

# Config: adjust counts as desired
NUM_USERS = 100
NUM_PRODUCTS = 1500  # Max cats to fetch
NUM_PURCHASES = 200

# Tune seller ratio / inventory density
SELLER_FRACTION = 0.25        # fraction of users who are sellers
MIN_SELLERS_PER_PRODUCT = 1   # ensure every product has at least this many sellers
MAX_SELLERS_PER_PRODUCT = 5   # max sellers per product
MAX_INV_QTY = 10              # max inventory quantity per seller-product
MAX_CART_ITEMS = 3            # max cart entries to create per buyer
MAX_ITEMS_PER_ORDER = 4       # items per purchase (1..MAX)

Faker.seed(0)
fake = Faker()
random.seed(0)

def get_csv_writer(f):
    return csv.writer(f, dialect='unix', quoting=csv.QUOTE_MINIMAL)

def safe_address(addr: str) -> str:
    # replace newlines with commas so COPY stays well-formed
    return addr.replace('\n', ', ')

def gen_users(num_users):
    users = []
    bio_options = [
        "Above average cat enjoyer",
        "Professional feline enthusiast",
        "Dedicated to finding the perfect cat for every occasion",
        "Cat collector extraordinaire",
        "Part-time cat whisperer, full-time cat admirer",
        "I love Chat-GPT but I like cats more"
    ]
    with open('db/generated/Users.csv', 'w') as f:
        writer = get_csv_writer(f)
        writer.writerow(['id', 'firstname', 'lastname', 'email', 'password', 'address', 'balance', 'bio'])
        print("Adding thomas")

        writer.writerow([
            0,  # id
            'Thomas',  # firstname
            'Lee',  # lastname
            'thomas15@yahoo.com',  # email
            generate_password_hash('pass0'),  # password
            fake.address().replace('\n', ', '),  # address
            f"{random.uniform(0, 1000):.2f}",  # balance
            "Avid fan of cats that say meow"  # bio
        ])
        users.append({'id': 0, 'firstname': 'Thomas', 'lastname': 'Lee', 'email': 'thomas15@yahoo.com'})

        print('Generating Users...', end=' ', flush=True)
        for uid in range(1, num_users + 1):
            if uid % 10 == 0:
                print(uid, end=' ', flush=True)
            profile = fake.simple_profile()
            email = profile['mail']
            plain_password = f'pass{uid}'
            password = generate_password_hash(plain_password)
            name_components = profile['name'].split(' ')
            firstname = name_components[0]
            lastname = name_components[-1]
            address = safe_address(fake.address())
            balance = f"{random.uniform(0, 1000):.2f}"
            bio = random.choice(bio_options)
            # order: id, firstname, lastname, email, password, address, balance, bio
            writer.writerow([uid, firstname, lastname, email, password, address, balance, bio])
            users.append({'id': uid, 'firstname': firstname, 'lastname': lastname, 'email': email})
        print(f'\n{num_users} users generated')
    return users

def load_products_from_csv():
    """Load products from the generated Products.csv"""
    products = []
    with open('db/generated/Products.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append({
                'id': int(row['id']),
                'name': row['name'],
                'category': row['category']
            })
    print(f'Loaded {len(products)} products from Products.csv')
    return products

def gen_sellers(users):
    seller_count = max(1, int(len(users) * SELLER_FRACTION))
    sellers = random.sample([u['id'] for u in users], seller_count)
    print(f'Chosen {len(sellers)} sellers out of {len(users)} users')
    return sellers

def gen_inventory(sellers, products):
    """
    Build inventory ensuring EVERY product has at least MIN_SELLERS_PER_PRODUCT sellers.
    Also write Inventory.csv rows: seller_id, product_id, quantity, price
    """
    product_to_sellers = {p['id']: [] for p in products}
    
    with open('db/generated/Inventory.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Generating Inventory...', end=' ', flush=True)
        
        # First pass: ensure every product has at least MIN_SELLERS_PER_PRODUCT sellers
        for i, prod in enumerate(products):
            if i % 100 == 0:
                print(i, end=' ', flush=True)
            
            # Determine how many sellers for this product
            num_sellers = random.randint(MIN_SELLERS_PER_PRODUCT, 
                                        min(MAX_SELLERS_PER_PRODUCT, len(sellers)))
            
            # Select random sellers for this product
            product_sellers = random.sample(sellers, num_sellers)
            
            for seller_id in product_sellers:
                qty = random.randint(1, MAX_INV_QTY)  # Ensure at least 1
                price = f"{random.uniform(5, 1000):.2f}"
                
                writer.writerow([seller_id, prod['id'], qty, price])
                product_to_sellers[prod['id']].append({'seller_id': seller_id, 'qty': qty})
        
        print('\nInventory written')
    
    # Verify all products have sellers
    products_without_sellers = [pid for pid, sellers_list in product_to_sellers.items() 
                               if not sellers_list]
    if products_without_sellers:
        print(f'WARNING: {len(products_without_sellers)} products have no sellers!')
    else:
        print(f'✓ All {len(products)} products have at least one seller')
    
    return product_to_sellers

def gen_carts(users, product_to_sellers):
    """
    Generate Carts.csv with buyer_id (account_id), product_id, seller_id, quantity
    """
    cart_rows = []
    with open('db/generated/Carts.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Generating Carts...', end=' ', flush=True)
        for i, user in enumerate(users):
            if i % 10 == 0:
                print(i, end=' ', flush=True)
            # random chance buyer has cart items
            if random.random() < 0.5:
                items = random.randint(1, min(10, MAX_CART_ITEMS))
                for _ in range(items):
                    # pick a random product that has sellers
                    prod_candidates = [pid for pid, sellers in product_to_sellers.items() if sellers]
                    if not prod_candidates:
                        continue
                    pid = random.choice(prod_candidates)
                    sellers_for_pid = [s for s in product_to_sellers[pid] if s['qty'] > 0]
                    if not sellers_for_pid:
                        sellers_for_pid = product_to_sellers[pid]
                        if not sellers_for_pid:
                            continue
                    seller_entry = random.choice(sellers_for_pid)
                    qty = random.randint(1, min(5, seller_entry['qty'] if seller_entry['qty']>0 else 5))
                    writer.writerow([user['id'], pid, seller_entry['seller_id'], qty])
                    cart_rows.append((user['id'], pid, seller_entry['seller_id'], qty))
        print('\nCarts written')
    return cart_rows

def gen_purchases_and_order_items(num_purchases, users, products, product_to_sellers):
    """
    Write Purchases.csv and Order_items.csv
    """
    purchases_rows = []
    order_items_rows = []
    
    def find_seller_for_product(pid, desired_qty=1):
        sellers = product_to_sellers.get(pid, [])
        # prefer sellers with sufficient qty
        for idx, s in enumerate(sellers):
            if s['qty'] >= desired_qty and s['qty'] > 0:
                return s, idx
        # fallback: any seller (even zero qty)
        if sellers:
            return sellers[0], 0
        return None, None
    
    with open('db/generated/Purchases.csv', 'w') as pf, open('db/generated/Order_items.csv', 'w') as of:
        p_writer = get_csv_writer(pf)
        o_writer = get_csv_writer(of)
        print('Generating Purchases and Order_items...', end=' ', flush=True)
        
        purchase_id = 0  # Start from 0 and only increment for successful purchases
        attempts = 0
        max_attempts = num_purchases * 3 # Try up to 3x the desired number
        
        while purchase_id < num_purchases and attempts < max_attempts:
            attempts += 1
            
            if purchase_id % 10 == 0 and purchase_id > 0:
                print(purchase_id, end=' ', flush=True)
            
            buyer = random.choice(users)
            buyer_id = buyer['id']
            address = safe_address(fake.address())
            created_at = fake.date_time_between(start_date='-1y', end_date='now').replace(tzinfo=timezone.utc).isoformat()
            
            num_items = random.randint(1, MAX_ITEMS_PER_ORDER)
            items_for_this_purchase = []
            item_attempts = 0
            
            while len(items_for_this_purchase) < num_items and item_attempts < num_items * 4:
                item_attempts += 1
                pid = random.choice(products)['id']
                seller_entry, idx = find_seller_for_product(pid, desired_qty=1)
                if seller_entry is None:
                    continue
                
                max_possible = seller_entry['qty'] if seller_entry['qty'] > 0 else 1
                qty = random.randint(1, min(3, max_possible))
                
                unit_price = round(random.uniform(5, 1000), 2)
                items_for_this_purchase.append({
                    'seller_id': seller_entry['seller_id'],
                    'product_id': pid,
                    'unit_price': unit_price,
                    'quantity': qty,
                    'created_at': created_at
                })
                
                if seller_entry['qty'] >= qty:
                    product_to_sellers[pid][idx]['qty'] -= qty
                else:
                    product_to_sellers[pid][idx]['qty'] = 0
            
            # Only write purchase if we have at least one item
            if len(items_for_this_purchase) == 0 or purchase_id == 0:
                continue
            
            fulfillment_status = 0  # default pending
            
            # Write purchase row with current purchase_id
            p_writer.writerow([purchase_id, address, created_at, buyer_id, fulfillment_status])
            purchases_rows.append({'purchase_id': purchase_id, 'buyer_id': buyer_id})
            
            # Write order items with matching purchase_id
            used_keys = set()
            for item in items_for_this_purchase:
                key = (purchase_id, item['seller_id'], item['product_id'])
                if key in used_keys:
                    continue
                o_writer.writerow([purchase_id, item['seller_id'], item['product_id'], item['quantity'], 0])
                order_items_rows.append({
                    'purchase_id': purchase_id,
                    'seller_id': item['seller_id'],
                    'product_id': item['product_id'],
                    'qty': item['quantity']
                })
                used_keys.add(key)
            
            # Only increment purchase_id after successfully writing everything
            purchase_id += 1
        
        print(f'\nPurchases and Order_items written ({purchase_id} purchases)')
    
    return purchases_rows, order_items_rows

def main():
    # Generate cat products first
    print('=== Generating Cat Products ===')
    num_products_generated = gen_cat_products(
        output_file='db/generated/Products.csv',
        max_cats=NUM_PRODUCTS,
        sayings=["meow", "hello", "goodbye", "prr"]
    )
    
    print(f'\n=== Generated {num_products_generated} cat products ===\n')
    
    # Load the generated products
    products = load_products_from_csv()
    
    # Generate other data
    users = gen_users(NUM_USERS)
    sellers = gen_sellers(users)
    product_to_sellers = gen_inventory(sellers, products)
    gen_carts(users, product_to_sellers)
    gen_purchases_and_order_items(NUM_PURCHASES, users, products, product_to_sellers)
    
    print('\n=== All CSV files generated ===')
    print('- db/generated/Users.csv')
    print('- db/generated/Products.csv')
    print('- db/generated/Inventory.csv')
    print('- db/generated/Carts.csv')
    print('- db/generated/Purchases.csv')
    print('- db/generated/Order_items.csv')

if __name__ == '__main__':
    main()