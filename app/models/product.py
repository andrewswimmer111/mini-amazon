from flask import current_app as app


class Product:
    def __init__(self, id, name, description, price, category=None):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.category = category

    @staticmethod
    def get_with_id(id):
        rows = app.db.execute('''
            SELECT *
            FROM Products
            WHERE id = :id
            ''',
        id=id
        )
        return Product(*(rows[0])) if rows is not None else None

    @staticmethod
    def get_all():
        rows = app.db.execute('''
            SELECT *
            FROM Products
            ''',
        ) 
        return [Product(*row) for row in rows]

    @staticmethod
    def get_all_available():
        """Get all products that are available in inventory (have at least one seller with stock)."""
        rows = app.db.execute('''
            SELECT DISTINCT p.*
            FROM Products p
            INNER JOIN Inventory i ON p.id = i.product_id
            WHERE i.quantity > 0
            ''',
        ) 
        return [Product(*row) for row in rows]

    @staticmethod 
    def get_k_most_expensive(k: int):
        rows = app.db.execute('''
            SELECT * 
            FROM Products
            ORDER BY price DESC
            LIMIT :k
            ''', 
        k=k
        )
        return [Product(*row) for row in rows]

    @staticmethod 
    def get_k_most_expensive_available(k: int):
        """Get k most expensive products that are available in inventory."""
        rows = app.db.execute('''
            SELECT DISTINCT p.*
            FROM Products p
            INNER JOIN Inventory i ON p.id = i.product_id
            WHERE i.quantity > 0
            ORDER BY p.price DESC
            LIMIT :k
            ''', 
        k=k
        )
        return [Product(*row) for row in rows]