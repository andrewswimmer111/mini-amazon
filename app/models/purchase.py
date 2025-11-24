from flask import current_app as app


class Purchase:
    def __init__(self, purchase_id, address, date, buyer_id, fulfillment_status, items, totalprice):
        self.purchase_id = purchase_id
        self.address = address
        self.date = date
        self.buyer_id = buyer_id
        self.fulfillment_status = fulfillment_status
        self.items = items #for specific items within purchase
        self.totalprice = totalprice #summed up from all items

    @staticmethod
    def get_all_purchanditems_for_user(buyer_id):
        rows = app.db.execute(
            '''
            SELECT pur.purchase_id,
                pur.address,
                pur.date,
                pur.fulfillment_status,
                prod.id AS product_id,
                prod.name AS product_name,
                prod.price,
                prod.category,
                l.quantity,
                l.seller_id,
                l.fulfillment_status AS item_fulfillment_status
            FROM Ledger l
            JOIN Purchases pur ON l.purchase_id = pur.purchase_id
            JOIN Products prod ON l.product_id = prod.id
            WHERE pur.buyer_id = :buyer_id
            ORDER BY pur.date DESC, pur.purchase_id
            ''',
            buyer_id=buyer_id
        )
        if not rows:
            return None

        # Group by purchase_id
        purchases = {}

        for row in rows:
            purchase_id = row[0]
            if purchase_id not in purchases:
                purchases[purchase_id] = {
                    'purchase_id': purchase_id,
                    'address': row[1],
                    'date': row[2],
                    'buyer_id': buyer_id,
                    'fulfillment_status': row[3],
                    'items': [],
                    'totalprice': 0.0  # initialize total cost
                } #this creates a dictionary item in the purchases dictionary
                #each one represents a purchase, and it has keys to show attributes (items is a list of more dictionaries representing items)

            # extract item info
            item = {
                'product_id': row[4],
                'product_name': row[5],
                'price': float(row[6]),
                'category': row[7],
                'quantity': int(row[8]),
                'seller_id': row[9],
                'item_fulfillment_status': row[10],
            }

            purchases[purchase_id]['items'].append(item)

            # add to total cost
            purchases[purchase_id]['totalprice'] += item['price'] * item['quantity']

        # Convert to list of Purchase objects
        return [Purchase(**p) for p in purchases.values()]






#     @staticmethod
#     def get(purchase_id):
#         rows = app.db.execute('''
# SELECT *
# FROM Purchases
# WHERE purchase_id = :purchase_id
# ''',
#                               purchase_id=purchase_id)
#         return Purchase(*(rows[0])) if rows else None


#     @staticmethod
#     def get_all_by_uid_since(buyer_id, since):
#         rows = app.db.execute('''
# SELECT *
# FROM Purchases
# WHERE buyer_id = :buyer_id
# AND date >= :since
# ORDER BY date DESC
# ''',
#                               buyer_id=buyer_id,
#                               since=since)
#         return [Purchase(*row) for row in rows]

    @staticmethod
    def create_from_cart(buyer_id, address):
        """Create a new purchase from the user's cart.
        
        1. Check buyer balance
        2. Create purchase record
        3. Copy cart items to ledger
        4. Update buyer and seller balances
        5. Clear the cart
        Returns the new Purchase object, 'insufficient_balance', or None if cart was empty.
        """
        # Start transaction
        with app.db.engine.begin() as conn:
            # Get cart items first to check if empty
            cart_items = app.db.execute('''
                SELECT c.seller_id, c.product_id, c.quantity
                FROM Cart c
                WHERE c.account_id = :uid
            ''', uid=buyer_id)
            
            if not cart_items:
                return None

            # Calculate total price first
            items = []
            totalprice = 0.0
            seller_totals = {}  # Track total amount per seller

            for seller_id, product_id, quantity in cart_items:
                prod_rows = app.db.execute('''
                    SELECT id, name, price, category
                    FROM Products
                    WHERE id = :pid
                ''', pid=product_id)
                if prod_rows:
                    prod = prod_rows[0]
                    prod_name = prod[1]
                    prod_price = float(prod[2]) if prod[2] is not None else 0.0
                    prod_category = prod[3]
                else:
                    prod_name = None
                    prod_price = 0.0
                    prod_category = None

                item = {
                    'product_id': product_id,
                    'product_name': prod_name,
                    'price': prod_price,
                    'category': prod_category,
                    'quantity': int(quantity),
                    'seller_id': seller_id,
                    'item_fulfillment_status': 1,
                }
                items.append(item)
                item_total = prod_price * int(quantity)
                totalprice += item_total
                
                # Track seller totals
                if seller_id not in seller_totals:
                    seller_totals[seller_id] = 0.0
                seller_totals[seller_id] += item_total

            # Check buyer balance
            buyer_balance_rows = app.db.execute('''
                SELECT balance
                FROM Users
                WHERE id = :uid
            ''', uid=buyer_id)
            
            if not buyer_balance_rows:
                return None
            
            buyer_balance = float(buyer_balance_rows[0][0]) if buyer_balance_rows[0][0] is not None else 0.0
            
            # Check if balance is sufficient
            if buyer_balance < totalprice:
                return 'insufficient_balance'

            # Create the purchase record with fulfillment_status=1
            purchase_rows = app.db.execute('''
                INSERT INTO Purchases (buyer_id, address, fulfillment_status)
                VALUES (:uid, :addr, 1)
                RETURNING purchase_id, buyer_id, date, address, fulfillment_status
            ''', uid=buyer_id, addr=address)
            
            if not purchase_rows:
                return None
            
            row = purchase_rows[0]
            purchase_id = row[0]
            buyer = row[1]
            date = row[2]
            address_db = row[3]
            fulfillment_status = row[4]

            # Insert ledger entries
            for seller_id, product_id, quantity in cart_items:
                app.db.execute('''
                    INSERT INTO Ledger
                    (purchase_id, seller_id, product_id, quantity, fulfillment_status)
                    VALUES (:pid, :sid, :prod_id, :qty, 1)
                ''', pid=purchase_id, sid=seller_id,
                     prod_id=product_id, qty=quantity)

            # Update buyer balance (decrement)
            app.db.execute('''
                UPDATE Users
                SET balance = balance - :amount
                WHERE id = :uid
            ''', amount=totalprice, uid=buyer_id)

            # Update seller balances (increment)
            for seller_id, seller_total in seller_totals.items():
                app.db.execute('''
                    UPDATE Users
                    SET balance = balance + :amount
                    WHERE id = :sid
                ''', amount=seller_total, sid=seller_id)

            # Clear the cart
            app.db.execute('''
                DELETE FROM Cart
                WHERE account_id = :uid
            ''', uid=buyer_id)

            return Purchase(purchase_id=purchase_id,
                            address=address_db,
                            date=date,
                            buyer_id=buyer,
                            fulfillment_status=fulfillment_status,
                            items=items,
                            totalprice=totalprice)
