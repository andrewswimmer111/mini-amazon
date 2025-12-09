from decimal import Decimal
from flask import current_app as app


class CartItem:
    def __init__(self, account_id, product_id, seller_id, quantity,
                 name, description, price, seller_firstname, seller_lastname):
        self.account_id = account_id
        self.product_id = product_id
        self.seller_id = seller_id
        self.quantity = quantity
        self.name = name
        self.description = description
        self.price = Decimal(price) if price is not None else Decimal('0.00')
        self.seller_firstname = seller_firstname
        self.seller_lastname = seller_lastname

    @property
    def seller_name(self):
        return f"{self.seller_firstname} {self.seller_lastname}".strip()

    @property
    def subtotal(self):
        return self.price * int(self.quantity)


class Cart:

    @staticmethod
    def get_user_cart(user_id):
        rows = app.db.execute('''
            SELECT c.account_id, c.product_id, c.seller_id, c.quantity,
                   p.name, p.description, i.price, u.firstname, u.lastname
            FROM Cart c
            JOIN Products p ON c.product_id = p.id
            JOIN Inventory i ON c.product_id = i.product_id AND c.seller_id = i.seller_id
            JOIN Users u ON c.seller_id = u.id
            WHERE c.account_id = :uid
            ''',
            uid=user_id)

        if not rows:
            return []

        return [CartItem(*row) for row in rows]

    @staticmethod
    def get_cart_item_count(user_id):
        rows = app.db.execute('''
            SELECT COALESCE(SUM(quantity), 0)
            FROM Cart
            WHERE account_id = :uid
            ''', uid=user_id)
        if not rows:
            return 0
        return int(rows[0][0]) if rows[0][0] is not None else 0

    @staticmethod
    def get_cart_total(user_id):
        rows = app.db.execute('''
            SELECT COALESCE(SUM(c.quantity * i.price), 0)
            FROM Cart c
            JOIN Inventory i ON c.product_id = i.product_id AND c.seller_id = i.seller_id
            WHERE c.account_id = :uid
            ''', uid=user_id)
        if not rows:
            return Decimal('0.00')
        total = rows[0][0]
        return Decimal(total) if total is not None else Decimal('0.00')

    @staticmethod
    def format_cart_items(user_id):
        items = Cart.get_user_cart(user_id)
        formatted = []
        for it in items:
            formatted.append({
                'product_id': it.product_id,
                'name': it.name,
                'description': it.description,
                'seller_id': it.seller_id,
                'seller_name': it.seller_name,
                'quantity': int(it.quantity),
                'price': it.price,
                'subtotal': it.subtotal
            })
        return formatted

    @staticmethod
    def get_default_seller(product_id):
        rows = app.db.execute('''
            SELECT seller_id
            FROM Inventory
            WHERE product_id = :pid
              AND quantity > 0
            LIMIT 1
        ''', pid=product_id)
        if not rows:
            return None
        return int(rows[0][0])

    @staticmethod
    def add_item(user_id, product_id, seller_id, quantity=1):
        print(f"[Cart.add_item] Adding to cart: user={user_id}, product={product_id}, seller={seller_id}, qty={quantity}")
        rows = app.db.execute('''
            INSERT INTO Cart (account_id, product_id, seller_id, quantity)
            VALUES (:uid, :pid, :sid, :qty)
            ON CONFLICT (account_id, product_id, seller_id)
            DO UPDATE SET quantity = Cart.quantity + EXCLUDED.quantity
            RETURNING quantity
        ''', uid=user_id, pid=product_id, sid=seller_id, qty=quantity)

        if not rows:
            return None
        return int(rows[0][0])

    @staticmethod
    def update_item(user_id, product_id, seller_id, quantity):
        if int(quantity) <= 0:
            return Cart.remove_item(user_id, product_id, seller_id)

        rows = app.db.execute('''
            UPDATE Cart
            SET quantity = :qty
            WHERE account_id = :uid
              AND product_id = :pid
              AND seller_id = :sid
            RETURNING quantity
        ''', uid=user_id, pid=product_id, sid=seller_id, qty=quantity)

        if not rows:
            return None
        return int(rows[0][0])

    @staticmethod
    def remove_item(user_id, product_id, seller_id):
        rc = app.db.execute('''
            DELETE FROM Cart
            WHERE account_id = :uid
              AND product_id = :pid
              AND seller_id = :sid
        ''', uid=user_id, pid=product_id, sid=seller_id)

        return rc > 0
