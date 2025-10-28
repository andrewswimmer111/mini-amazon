from flask import current_app as app


class Purchase:
    def __init__(self, purchase_id, buyer_id, date, address, fulfillment_status):
        self.purchase_id = purchase_id
        self.buyer_id = buyer_id
        self.date = date
        self.address = address
        self.fulfillment_status = fulfillment_status


    @staticmethod
    def get(id):
        rows = app.db.execute('''
SELECT id, uid, pid, time_purchased
FROM Purchases
WHERE id = :id
''',
                              id=id)
        return Purchase(*(rows[0])) if rows else None

    @staticmethod
    def get_all_by_uid_since(uid, since):
        rows = app.db.execute('''
SELECT purchase_id, buyer_id, date, address, fulfillment_status
FROM Purchases
WHERE buyer_id = :uid
AND date >= :since
ORDER BY date DESC
''', uid=uid, since=since)

        return [Purchase(*row) for row in rows]

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
