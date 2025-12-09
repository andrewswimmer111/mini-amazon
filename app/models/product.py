from flask import current_app as app


class Product:
    def __init__(self, id, name, description, image=None, category=None, created_by=None):
        self.id = id
        self.name = name
        self.description = description
        self.image = image
        self.category = category
        self.created_by = created_by

    @staticmethod
    def get_with_id(id):
        rows = app.db.execute('''
            SELECT id, name, description, image, category, created_by
            FROM Products
            WHERE id = :id
            ''',
        id=id
        )
        return Product(*(rows[0])) if rows is not None else None

    @staticmethod
    def get_all():
        # Only return products that have at least one seller
        rows = app.db.execute('''
            SELECT DISTINCT p.id, p.name, p.description, p.image, p.category, p.created_by
            FROM Products p
            INNER JOIN Inventory i ON p.id = i.product_id
        ''') 
        return [Product(*row) for row in rows]
    
    @staticmethod
    def get_categories():
        # Only show categories for products that have sellers
        rows = app.db.execute('''
            SELECT DISTINCT p.category
            FROM Products p
            INNER JOIN Inventory i ON p.id = i.product_id
            WHERE p.category IS NOT NULL
            ORDER BY p.category
        ''')
        return [row[0] for row in rows] if rows else []

    @staticmethod
    def create(name, description, category, image=None, created_by=None):
        try:
            rows = app.db.execute('''
                INSERT INTO PRODUCTS(name, description, image, category, created_by)
                VALUES (:name, :description, :image, :category, :created_by)
                RETURNING id
                ''',
                name=name, description=description, image=image, category=category, created_by=created_by)
            id = rows[0][0]
            return Product.get_with_id(id)
        except Exception as e:
            print(str(e))
            return None
        

    @staticmethod
    def update(product_id, name, description, category, image=None, created_by=None):
        rows = app.db.execute('''
            UPDATE Products
            SET name = :name,
                description = :description,
                image = :image,
                category = :category,
                created_by = :created_by
            WHERE id = :product_id
            RETURNING id
        ''',
        name=name, description=description, image=image, category=category, created_by=created_by, product_id=product_id)

        if not rows:
            return None

        id = rows[0][0]
        # build and return a Product object (match the shape your app uses)
        return Product.get_with_id(id)

    # Filters below
    @staticmethod
    def _build_filter_sql(category=None, keyword=None):
        # Only show products that have at least one seller in Inventory
        sql = ["SELECT DISTINCT p.id, p.name, p.description, p.image, p.category, p.created_by FROM Products p"]
        sql.append("INNER JOIN Inventory i ON p.id = i.product_id")
        conditions = []
        params = {}

        if category is not None:
            conditions.append("p.category = :category")
            params["category"] = category
        
        if keyword is not None: 
            conditions.append("(p.name ILIKE :keyword OR p.description ILIKE :keyword)")
            params["keyword"] = f"%{keyword}%"
        
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        else:
            where_clause = ""
        
        return " ".join(sql) + " " + where_clause, params

    @staticmethod
    def count_with_filters(category=None, keyword=None):
        sql_query, params = Product._build_filter_sql(category, keyword)
        # Convert SELECT to COUNT
        sql = sql_query.replace("SELECT DISTINCT p.id, p.name, p.description, p.image, p.category, p.created_by", "SELECT COUNT(DISTINCT p.id)")
        row = app.db.execute(sql, params)[0]
        if row is None:
            return 0
        else:
            return int(row[0])
        
    
    @staticmethod
    def get_with_filters(
        category: str = None,
        keyword: str = None,
        sortBy: str = None,
        sortDir: str = None,
        limit: int = None,
        offset: int = None
    ): 

        # Param checks
        if sortDir and sortDir.lower() not in {"asc", "desc"}:
            raise ValueError("sortDir must be 'asc' or 'desc'")
        
        if sortBy and sortBy.lower() not in {"name"}:
            raise ValueError("sortBy must be 'name'")
        
        # Build SQL
        sql_query, params = Product._build_filter_sql(category, keyword)
        sql_parts = [
            sql_query,
            f"ORDER BY p.{sortBy} {sortDir.upper()}" if sortBy else "ORDER BY p.id"
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