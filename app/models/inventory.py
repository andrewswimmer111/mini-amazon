# app/models/inventory.py
from flask import current_app


class InventoryItem:
    def __init__(self, id_, seller_id, product_id, quantity, product=None):
        self.id = id_
        self.seller_id = seller_id
        self.product_id = product_id
        self.quantity = quantity
        self.product = product or {}

    @classmethod
    def from_row(cls, row):
        # handle dict-like or tuple-like row
        try:
            id_ = row['id']
            seller_id = row['seller_id']
            product_id = row['product_id']
            quantity = row['quantity']
            product = {}
            if 'name' in row and 'price' in row:
                product = {"name": row['name'], "price": float(row['price'])}
            return cls(id_, seller_id, product_id, quantity, product)
        except Exception:
            # tuple fallback
            id_, seller_id, product_id, quantity = row[0], row[1], row[2], row[3]
            product = {}
            if len(row) >= 6:
                product = {"name": row[4], "price": float(row[5])}
            return cls(id_, seller_id, product_id, quantity, product)

    def to_dict(self):
        return {
            "id": self.id,
            "seller_id": self.seller_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "product": self.product,
        }

    @classmethod
    def get_for_seller(cls, seller_id):
        sql = """
        SELECT i.id, i.seller_id, i.product_id, i.quantity, p.name, p.price
        FROM inventory i
        LEFT JOIN products p ON p.id = i.product_id
        WHERE i.seller_id = :seller_id
        ORDER BY i.id;
        """
        rows = current_app.db.execute(sql, seller_id=seller_id)
        return [cls.from_row(r) for r in rows]
