# gen_data.py
from werkzeug.security import generate_password_hash
import csv
import random
from faker import Faker
from datetime import datetime, timezone

# Config: adjust counts as desired
NUM_USERS = 10
NUM_PRODUCTS = 20
NUM_PURCHASES = 20

# Tune seller ratio / inventory density
SELLER_FRACTION = 0.25        # fraction of users who are sellers
PRODUCTS_PER_SELLER = 2     # how many distinct products each seller stocks (avg)
MAX_INV_QTY = 10             # max inventory quantity per seller-product
MAX_CART_ITEMS = 3           # max cart entries to create per buyer
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
    with open('Users.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Generating Users...', end=' ', flush=True)
        for uid in range(num_users):
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
            # order: id, firstname, lastname, email, password, address, balance
            writer.writerow([uid, firstname, lastname, email, password, address, balance])
            users.append({'id': uid, 'firstname': firstname, 'lastname': lastname, 'email': email})
        print(f'\n{num_users} users generated')
    return users


def gen_products(num_products):
    products = []
    with open('Products.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Generating Products...', end=' ', flush=True)
        for pid in range(num_products):
            if pid % 100 == 0:
                print(pid, end=' ', flush=True)
            name = fake.sentence(nb_words=4).rstrip('.')
            description = fake.paragraph(nb_sentences=2)

            # simple image URL placeholder
            # image_url = f'https://example.com/images/product_{pid}.jpg'
            
            category = random.choice(['A', 'B', 'C', 'D'])
            # order: id,name,description,category
            writer.writerow([pid, name, description, category])
            products.append({'id': pid, 'name': name})
        print(f'\n{num_products} products generated')
    return products


def gen_sellers(users):
    seller_count = max(1, int(len(users) * SELLER_FRACTION))
    sellers = random.sample([u['id'] for u in users], seller_count)
    print(f'Chosen {len(sellers)} sellers out of {len(users)} users')
    return sellers


def gen_inventory(sellers, products):
    """
    Build inventory: mapping product_id -> list of seller entries that stock it.
    Also write Inventory.csv rows: seller_id, product_id, quantity
    """
    product_to_sellers = {p['id']: [] for p in products}
    with open('Inventory.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Generating Inventory...', end=' ', flush=True)
        for i, seller_id in enumerate(sellers):
            if i % 10 == 0:
                print(i, end=' ', flush=True)
            # choose a subset of products to stock
            stocked = random.sample(products, k=min(PRODUCTS_PER_SELLER, len(products)))
            for prod in stocked:
                qty = random.randint(0, MAX_INV_QTY)
                price = f"{random.uniform(5, 1000):.2f}"
                if qty == 0:
                    # you may still want sellers listed with zero stock; include them
                    pass
                writer.writerow([seller_id, prod['id'], qty, price])
                product_to_sellers[prod['id']].append({'seller_id': seller_id, 'qty': qty})
        print('\nInventory written')
    return product_to_sellers


def gen_carts(users, product_to_sellers):
    """
    Generate carts.csv with buyer_id (account_id), product_id, seller_id, quantity
    Create up to MAX_CART_ITEMS distributed randomly among buyers.
    """
    cart_rows = []
    with open('Carts.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Generating Carts...', end=' ', flush=True)
        for i, user in enumerate(users):
            if i % 10 == 0:
                print(i, end=' ', flush=True)
            # random chance buyer has cart items
            if random.random() < 0.5:
                items = random.randint(1, min(10, MAX_CART_ITEMS))
                for _ in range(items):
                    # pick a random product that has at least one seller (non-empty sellers list)
                    prod_candidates = [pid for pid, sellers in product_to_sellers.items() if sellers]
                    if not prod_candidates:
                        continue
                    pid = random.choice(prod_candidates)
                    sellers_for_pid = [s for s in product_to_sellers[pid] if s['qty'] > 0]
                    if not sellers_for_pid:
                        # if no seller has stock, still pick a seller (qty may be zero)
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
    Write Purchases.csv and Order_items.csv in Ledger-friendly shape.
    Purchases.csv: purchase_id,address,date,buyer_id,fulfillment_status,total
    Order_items.csv: purchase_id,seller_id,product_id,quantity,fulfillment_status
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

    with open('Purchases.csv', 'w') as pf, open('Order_items.csv', 'w') as of:
        p_writer = get_csv_writer(pf)
        o_writer = get_csv_writer(of)
        print('Generating Purchases and Order_items...', end=' ', flush=True)

        for purchase_id in range(num_purchases):
            if purchase_id % 100 == 0:
                print(purchase_id, end=' ', flush=True)
            buyer = random.choice(users)
            buyer_id = buyer['id']
            address = safe_address(fake.address())
            created_at = fake.date_time_between(start_date='-1y', end_date='now').replace(tzinfo=timezone.utc).isoformat()
            num_items = random.randint(1, MAX_ITEMS_PER_ORDER)
            items_for_this_purchase = []

            attempts = 0
            while len(items_for_this_purchase) < num_items and attempts < num_items * 4:
                attempts += 1
                pid = random.choice(products)['id']
                seller_entry, idx = find_seller_for_product(pid, desired_qty=1)
                if seller_entry is None:
                    continue
                max_possible = seller_entry['qty'] if seller_entry['qty'] > 0 else 1
                qty = random.randint(1, min(3, max_possible))
                prod_info = next((p for p in products if p['id'] == pid), None)
                if prod_info is None:
                    continue
                # Get price from inventory (we'll need to track this differently)
                # For now, generate a random price
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

            if len(items_for_this_purchase) == 0:
                continue

            fulfillment_status = 0  # default pending
            # Write purchase row: purchase_id,address,date,buyer_id,fulfillment_status,total
            p_writer.writerow([purchase_id, address, created_at, buyer_id, fulfillment_status])
            purchases_rows.append({'purchase_id': purchase_id, 'buyer_id': buyer_id})

            # *** IMPORTANT: write Order_items.csv in Ledger shape (no id, no unit_price, created_at)
            # Order_items.csv columns: purchase_id, seller_id, product_id, quantity, fulfillment_status
            used_keys = set()
            for item in items_for_this_purchase:
                if (purchase_id, item['seller_id'], item['product_id']) in used_keys:
                    continue
                o_writer.writerow([purchase_id, item['seller_id'], item['product_id'], item['quantity'], 0])
                order_items_rows.append({
                    'purchase_id': purchase_id,
                    'seller_id': item['seller_id'],
                    'product_id': item['product_id'],
                    'qty': item['quantity']
                })
                used_keys.add((purchase_id, item['seller_id'], item['product_id']))

        print('\nPurchases and Order_items written')

    return purchases_rows, order_items_rows


def main():
    users = gen_users(NUM_USERS)
    products = gen_products(NUM_PRODUCTS)
    sellers = gen_sellers(users)
    product_to_sellers = gen_inventory(sellers, products)
    gen_carts(users, product_to_sellers)
    gen_purchases_and_order_items(NUM_PURCHASES, users, products, product_to_sellers)
    print('All CSV files generated: Users.csv, Products.csv, Inventory.csv, Carts.csv, Purchases.csv, Order_items.csv')


if __name__ == '__main__':
    main()
