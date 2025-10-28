# app/models/inventory.py
from flask import current_app




class InventoryItem:
    def __init__(self, seller_id, product_id, quantity, name=None, price=None):
        self.seller_id = seller_id
        self.product_id = product_id
        self.quantity = quantity
        self.product = {"name": name, "price": price}

    @classmethod
    def from_row(cls, row):
        try:
            seller_id = row['seller_id']
            product_id = row['product_id']
            quantity = row['quantity']
            name = row.get('name')
            price = float(row['price']) if 'price' in row and row['price'] is not None else None
            return cls(seller_id, product_id, quantity, name, price)
        except Exception:
            seller_id, product_id, quantity = row[0], row[1], row[2]
            name = None
            price = None
            if len(row) >= 5:
                name = row[3]
                price = float(row[4]) if row[4] is not None else None
            return cls(seller_id, product_id, quantity, name, price)

    def to_dict(self):
        return {
            "seller_id": self.seller_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "name": self.product.get("name"),
            "price": self.product.get("price"),
            "product": self.product,
        }

    @classmethod
    def get_for_seller(cls, seller_id):
        sql = """
        SELECT i.seller_id, i.product_id, i.quantity, p.name, p.price
        FROM inventory i
        LEFT JOIN products p ON p.id = i.product_id
        WHERE i.seller_id = :seller_id
        """
        rows = current_app.db.execute(sql, seller_id=seller_id)
        return [cls.from_row(r) for r in rows]
