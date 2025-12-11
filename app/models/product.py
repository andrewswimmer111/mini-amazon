from flask import current_app as app


class Product:
    def __init__(self, id, name, description, image=None, category=None, created_by=None, min_price=None, max_price=None):
        self.id = id
        self.name = name
        self.description = description
        self.image = image
        self.category = category
        self.created_by = created_by
        self.min_price = min_price
        self.max_price = max_price

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
    
    @staticmethod
    def delete_product(product_id):
        # Remove inventory entries referencing this product
        app.db.execute("""
            DELETE FROM Inventory
            WHERE product_id = :product_id
        """, product_id=product_id)

        # Delete the product
        app.db.execute("""
            DELETE FROM Products
            WHERE id = :product_id
        """, product_id=product_id)
        
    def getPriceRange(id):
        rows = app.db.execute('''
            SELECT 
                MIN(price) AS min_price,
                MAX(price) AS max_price
            FROM Inventory
            WHERE product_id = :id
        ''',
        id=id)

        # rows is a list of dictionaries; return the first row
        if rows:
            return rows[0]['min_price'], rows[0]['max_price']
        return None, None


    # Filters below
    @staticmethod
    def _build_filter_sql(category=None, keyword=None, min_price=None, max_price=None):
        sql = [
            "SELECT p.id, p.name, p.description, p.image, p.category, p.created_by,",
            "       MIN(i.price) AS min_price, MAX(i.price) AS max_price",
            "FROM Products p",
            "INNER JOIN Inventory i ON p.id = i.product_id"
        ]

        conditions = []
        params = {}

        if category is not None:
            conditions.append("p.category = :category")
            params["category"] = category
        
        if keyword is not None:
            conditions.append("(p.name ILIKE :keyword OR p.description ILIKE :keyword)")
            params["keyword"] = f"%{keyword}%"

        if min_price is not None:
            conditions.append("MIN(i.price) >= :min_price")
            params["min_price"] = min_price

        if max_price is not None:
            conditions.append("MIN(i.price) <= :max_price")
            params["max_price"] = max_price

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        # Must group by product to use MIN(i.price)
        sql.append(where_clause)
        sql.append("GROUP BY p.id, p.name, p.description, p.image, p.category, p.created_by")

        return "\n".join(sql), params


    @staticmethod
    def count_with_filters(category=None, keyword=None, min_price=None, max_price=None):
        sql_query, params = Product._build_filter_sql(category, keyword, min_price, max_price)

        # count distinct product IDs from grouped results
        sql = f"SELECT COUNT(*) FROM ({sql_query}) AS sub"
        
        row = app.db.execute(sql, params)[0]
        return int(row[0]) if row else 0

        
    
    @staticmethod
    def get_with_filters(
        category=None,
        keyword=None,
        min_price=None,
        max_price=None,
        sortBy=None,
        sortDir=None,
        limit=None,
        offset=None
    ):

        sql_query, params = Product._build_filter_sql(category, keyword, min_price, max_price)

        # Sorting
        if sortDir and sortDir.lower() not in {"asc", "desc"}:
            raise ValueError("sortDir must be 'asc' or 'desc'")

        if sortBy and sortBy.lower() not in {"name", "min_price", "max_price"}:
            raise ValueError("sortBy must be 'name' or 'min_price' or 'max_price'")

        sort_column = sortBy if sortBy else "p.id"
        sort_direction = sortDir.upper() if sortDir else "ASC"

        sql = f"{sql_query}\nORDER BY {sort_column} {sort_direction}"

        if limit is not None:
            sql += "\nLIMIT :limit"
            params["limit"] = limit

        if offset is not None:
            sql += "\nOFFSET :offset"
            params["offset"] = offset

        rows = app.db.execute(sql, params)
        return rows  # or build Product objects if needed
