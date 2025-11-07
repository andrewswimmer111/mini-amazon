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
        ''') 
        return [Product(*row) for row in rows]
    

    # Filters below
    @staticmethod 
    def get_k_most_expensive(k: int):
        rows = app.db.execute('''
            SELECT * 
            FROM Products
            ORDER BY price DESC
            LIMIT :k
        ''', k=k)
        return [Product(*row) for row in rows]
    
    @staticmethod
    def get_with_filters(category: None, keyword: None, minPrice: None, maxPrice: None, sortBy: None, sortDir: None, limit: None): 

        # Param checks
        if sortDir and sortDir.lower() not in {"asc", "desc"}:
            raise ValueError("sortDir must be 'asc' or 'desc'")
        
        if sortBy and sortBy.lower() not in {"price", "name"}:
            raise ValueError("sortBy be 'asc' or 'desc'")
        
        if limit and limit <= 0:
            raise ValueError("limit must be a positive integer")
        
        # Building SQL Query
        sql = ["SELECT * FROM Products p"]
        conditions = []
        params = {}

        if category is not None:
            conditions.append("p.category = :category")
            params["category"] = category
        
        if keyword is not None: 
            conditions.append("(p.name ILIKE :keyword OR p.description ILIKE :keyword)")
            params["keyword"] = f"%{keyword}%"
        
        if minPrice is not None:
            conditions.append("p.price >= :minPrice")
            params["minPrice"] = minPrice
        
        if maxPrice is not None:
            conditions.append("p.price <= :maxPrice")
            params["maxPrice"] = maxPrice
        
        if conditions:
            sql.append("WHERE " + " AND ".join(conditions))

        if sortBy is not None:
            sql.append(f"ORDER BY p.{sortBy} {sortDir.upper()}")

        if limit is not None:
            sql.append("LIMIT :limit")
            params["limit"] = limit
        
        full_query = "\n".join(sql)
        rows = app.db.execute(full_query, params)

        return [Product(*row) for row in rows]
    
    # Helpers below:
    @staticmethod
    def get_categories():
        rows = app.db.execute('''
            SELECT DISTINCT p.category
            FROM Products p
            ORDER BY p.category
        ''')
        return [row[0] for row in rows]