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
    
    @staticmethod
    def get_categories():
        rows = app.db.execute('''
            SELECT DISTINCT category
            FROM Products
            WHERE category IS NOT NULL
            ORDER BY category
        ''')
        return [row[0] for row in rows] if rows else []

    @staticmethod
    def create(name, description, price, category):
        try:
            rows = app.db.execute('''
                INSERT INTO PRODUCTS(name, description, price, category)
                VALUES (:name, :description, :price, :category)
                RETURNING id
                ''',
                name=name, description=description, price=price, category=category)
            id = rows[0][0]
            return Product.get_with_id(id)
        except Exception as e:
            print(str(e))
            return None
        

    def update(product_id, name, description, price, category):
        rows = app.db.execute('''
            UPDATE Products
            SET name = :name,
                description = :description,
                price = :price,
                category = :category
            WHERE id = :product_id
            RETURNING id
        ''',
        name=name, description=description, price=price, category=category, product_id=product_id)

        if not rows:
            return None

        id = rows[0][0]
        # build and return a Product object (match the shape your app uses)
        return Product.get_with_id(id)

    # Filters below
    @staticmethod
    def _build_filter_sql(category=None, keyword=None, minPrice=None, maxPrice=None):
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
            where_clause = "WHERE " + " AND ".join(conditions)
        else:
            where_clause = ""
        
        return where_clause, params

    @staticmethod
    def count_with_filters(category=None, keyword=None, minPrice=None, maxPrice=None):
        where_clause, params = Product._build_filter_sql(category, keyword, minPrice, maxPrice)
        sql = f"SELECT COUNT(*) FROM Products p {where_clause}"
        row = app.db.execute(sql, params)[0]
        if row is None:
            return 0
        else:
            return int(row[0])
        
    
    @staticmethod
    def get_with_filters(
        category: str = None,
        keyword: str = None,
        minPrice: float = None,
        maxPrice: float = None,
        sortBy: str = None,
        sortDir: str = None,
        limit: int = None,
        offset: int = None
    ): 

        # Param checks
        if sortDir and sortDir.lower() not in {"asc", "desc"}:
            raise ValueError("sortDir must be 'asc' or 'desc'")
        
        if sortBy and sortBy.lower() not in {"price", "name"}:
            raise ValueError("sortBy be 'asc' or 'desc'")
        
        # Build SQL
        where_clause, params = Product._build_filter_sql(category, keyword, minPrice, maxPrice)
        sql_parts = [
            f"SELECT * FROM Products p {where_clause}",
            f"ORDER BY p.{sortBy} {sortDir.upper()}"
        ]

        if limit is not None:
            sql_parts.append("LIMIT :limit")
            params["limit"] = int(limit)
            
        if offset is not None:
            sql_parts.append("OFFSET :offset")
            params["offset"] = int(offset)

        full_sql = "\n".join(sql_parts)
        rows = app.db.execute(full_sql, params)
        return [Product(*row) for row in rows]