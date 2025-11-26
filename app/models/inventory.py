# app/models/inventory.py
from flask import current_app as app


class InventoryItem:
    def __init__(self, seller_id, product_id, quantity, name=None, price=None, category=None):
        self.seller_id = seller_id
        self.product_id = product_id
        self.quantity = quantity
        self.product = {"name": name, "price": price, "category": category}

    @classmethod
    def from_row(cls, row):
        try:
            seller_id = row['seller_id']
            product_id = row['product_id']
            quantity = row['quantity']
            name = row.get('name')
            price = float(row['price']) if 'price' in row and row['price'] is not None else None
            category = row.get('category')
            return cls(seller_id, product_id, quantity, name, price, category)
        except Exception:
            seller_id, product_id, quantity = row[0], row[1], row[2]
            name = None
            price = None
            category = None
            if len(row) >= 5:
                name = row[3]
                price = float(row[4]) if row[4] is not None else None
            if len(row) >= 6:
                category = row[5]
            return cls(seller_id, product_id, quantity, name, price, category)

    def to_dict(self):
        return {
            "seller_id": self.seller_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "name": self.product.get("name"),
            "price": self.product.get("price"),
            "category": self.product.get("category"),
            "product": self.product,
        }

    @classmethod
    def get_for_seller(cls, seller_id):
        sql = """
        SELECT i.seller_id, i.product_id, i.quantity, p.name, p.price, p.category
        FROM inventory i
        LEFT JOIN products p ON p.id = i.product_id
        WHERE i.seller_id = :seller_id
        ORDER BY p.name
        """
        rows = app.db.execute(sql, seller_id=seller_id)
        return [cls.from_row(r) for r in rows]

    @staticmethod
    def get_sellers_from_product(product_id):
        rows = app.db.execute('''
                    SELECT * 
                    FROM Inventory i
                    WHERE i.product_id = :product_id
                    ''',
                product_id=product_id)
        return [InventoryItem(*row) for row in rows]

    @staticmethod
    def add_or_update(seller_id, product_id, quantity):
        """Add a product to inventory or update quantity if it already exists."""
        try:
            rows = app.db.execute('''
                INSERT INTO Inventory (seller_id, product_id, quantity)
                VALUES (:seller_id, :product_id, :quantity)
                ON CONFLICT (seller_id, product_id)
                DO UPDATE SET quantity = Inventory.quantity + EXCLUDED.quantity
                RETURNING seller_id, product_id, quantity
            ''',
            seller_id=seller_id, product_id=product_id, quantity=quantity)
            if rows:
                return InventoryItem(rows[0][0], rows[0][1], rows[0][2])
            return None
        except Exception as e:
            print("Error adding/updating inventory:", e)
            return None

    @staticmethod
    def set_quantity(seller_id, product_id, quantity):
        """Set the exact quantity for a product in inventory."""
        try:
            if quantity <= 0:
                # If quantity is 0 or negative, remove from inventory
                return InventoryItem.remove_from_inventory(seller_id, product_id)
            
            rows = app.db.execute('''
                UPDATE Inventory 
                SET quantity = :quantity
                WHERE seller_id = :seller_id AND product_id = :product_id
                RETURNING seller_id, product_id, quantity
            ''',
            seller_id=seller_id, product_id=product_id, quantity=quantity)
            if rows:
                return InventoryItem(rows[0][0], rows[0][1], rows[0][2])
            return None
        except Exception as e:
            print("Error setting inventory quantity:", e)
            return None

    @staticmethod
    def remove_from_inventory(seller_id, product_id):
        """Remove a product from seller's inventory entirely."""
        try:
            app.db.execute('''
                DELETE FROM Inventory
                WHERE seller_id = :seller_id AND product_id = :product_id
            ''',
            seller_id=seller_id, product_id=product_id)
            return True
        except Exception as e:
            print("Error removing from inventory:", e)
            return False

    @staticmethod
    def get_item(seller_id, product_id):
        """Get a specific inventory item."""
        try:
            rows = app.db.execute('''
                SELECT i.seller_id, i.product_id, i.quantity, p.name, p.price, p.category
                FROM Inventory i
                LEFT JOIN Products p ON p.id = i.product_id
                WHERE i.seller_id = :seller_id AND i.product_id = :product_id
            ''',
            seller_id=seller_id, product_id=product_id)
            if rows:
                return InventoryItem.from_row(rows[0])
            return None
        except Exception as e:
            print("Error getting inventory item:", e)
            return None

    @staticmethod
    def get_products_not_in_inventory(seller_id):
        """Get all products that the seller doesn't have in their inventory."""
        try:
            rows = app.db.execute('''
                SELECT p.id, p.name, p.description, p.price, p.category
                FROM Products p
                WHERE p.id NOT IN (
                    SELECT product_id FROM Inventory WHERE seller_id = :seller_id
                )
                ORDER BY p.name
            ''',
            seller_id=seller_id)
            return rows
        except Exception as e:
            print("Error getting products not in inventory:", e)
            return []
