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
        
        1. Create purchase record
        2. Copy cart items to ledger
        3. Clear the cart
        Returns the new Purchase object or None if cart was empty.
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

            # Create the purchase record with fulfillment_status=1
            purchase_rows = app.db.execute('''
                INSERT INTO Purchases (buyer_id, address, fulfillment_status)
                VALUES (:uid, :addr, 1)
                RETURNING purchase_id, buyer_id, date, address, fulfillment_status
            ''', uid=buyer_id, addr=address)
            
            if not purchase_rows:
                return None
            
            purchase = Purchase(*purchase_rows[0])
            
            # Copy cart items to ledger, also with fulfillment_status=1
            for seller_id, product_id, quantity in cart_items:
                app.db.execute('''
                    INSERT INTO Ledger
                    (purchase_id, seller_id, product_id, quantity, fulfillment_status)
                    VALUES (:pid, :sid, :prod_id, :qty, 1)
                ''', pid=purchase.purchase_id, sid=seller_id,
                     prod_id=product_id, qty=quantity)
            
            # Clear the cart
            app.db.execute('''
                DELETE FROM Cart
                WHERE account_id = :uid
            ''', uid=buyer_id)
            
            return purchase
