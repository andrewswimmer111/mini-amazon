from flask_login import UserMixin
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash

from .. import login


class User(UserMixin):
    def __init__(self, id, email, firstname, lastname, address=None, balance=None, bio=None):
        self.id = id
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.address = address
        self.balance = balance if balance is not None else 0.0
        self.bio = bio

    @staticmethod
    def get_by_auth(email, password):
        rows = app.db.execute("""
SELECT password, id, email, firstname, lastname, address, balance, bio
FROM Users
WHERE email = :email
""",
                              email=email)
        if not rows:  # email not found
            return None
        elif not check_password_hash(rows[0][0], password):
            # incorrect password
            return None
        else:
            return User(*(rows[0][1:]))

    @staticmethod
    def email_exists(email):
        rows = app.db.execute("""
SELECT email
FROM Users
WHERE email = :email
""",
                              email=email)
        return len(rows) > 0

    @staticmethod
    def register(firstname, lastname, email, password, address):
        try:
            rows = app.db.execute("""
INSERT INTO Users(firstname, lastname, email, password, address, balance, bio)
VALUES(:firstname, :lastname, :email, :password, :address, 0.0, "")
RETURNING id
""",
                                  email=email,
                                  password=generate_password_hash(password),
                                  firstname=firstname, lastname=lastname, address=address)
            id = rows[0][0]
            return User.get(id)
        except Exception as e:
            # likely email already in use; better error checking and reporting needed;
            # the following simply prints the error to the console:
            print(str(e))
            return None

    @staticmethod
    @login.user_loader
    def get(id):
        rows = app.db.execute("""
SELECT id, email, firstname, lastname, address, balance, bio
FROM Users
WHERE id = :id
""",
                              id=id)
        return User(*(rows[0])) if rows else None


    @staticmethod
    def update(user_id, email, firstname, lastname, address, bio, password=None):
        # Check for email uniqueness
        rows = app.db.execute("""
            SELECT id FROM Users WHERE email = :email AND id != :uid
        """, email=email, uid=user_id)
        if rows:
            return "email_taken"

        # Update password if provided
        if password:
            hashed_pw = generate_password_hash(password)
            app.db.execute("""
                UPDATE Users
                SET email = :email,
                    firstname = :firstname,
                    lastname = :lastname,
                    address = :address,
                    password = :password
                WHERE id = :uid
            """, email=email, firstname=firstname, lastname=lastname,
            address=address, password=hashed_pw, uid=user_id)
        else:
            app.db.execute("""
                UPDATE Users
                SET email = :email,
                    firstname = :firstname,
                    lastname = :lastname,
                    address = :address
                    bio = :bio
                WHERE id = :uid
            """, email=email, firstname=firstname, lastname=lastname,
            address=address, bio=bio, uid=user_id)

        return "ok"
    
    @staticmethod
    def topup(user_id, amount):
        """Add amount to user's balance."""
        app.db.execute("""
                        UPDATE Users
                        SET balance = COALESCE(balance, 0) + :amount
                       WHERE id= :id
                    """,
                       amount=amount, id=user_id)
        return "ok"
    @staticmethod
    def withdraw(user_id, amount):
        """Deduct amount from user's balance."""
        app.db.execute("""
                        UPDATE Users
                        SET balance = COALESCE(balance, 0) - :amount
                       WHERE id= :id
                    """,
                       amount=amount, id=user_id)
        return "ok"
    
    @staticmethod
    def getTotalSpending(userId):
        """Gets sum of prices (quantity * price) for all items bought by the user.

        Note: uses Inventory.price at query time (may differ from price at purchase time).

        Worth of Purchased Items
        """
        rows = app.db.execute("""
            SELECT SUM(l.quantity * COALESCE(i.price, 0))
            FROM Ledger l
            JOIN Purchases p ON p.purchase_id = l.purchase_id
            LEFT JOIN Inventory i
            ON i.seller_id = l.seller_id
            AND i.product_id = l.product_id
            WHERE p.buyer_id = :id
        """, id=userId)

        return float(rows[0][0]) if rows and rows[0][0] is not None else 0.0


    @staticmethod
    def getTotalProfit(userId):
        """Gets sum of revenue (quantity * price) for all items sold by the user.

        Note: uses Inventory.price at query time (may differ from price at purchase time).

        Value of Sold Inventory (at current prices)
        """
        rows = app.db.execute("""
            SELECT SUM(l.quantity * COALESCE(i.price, 0))
            FROM Ledger l
            LEFT JOIN Inventory i
            ON i.seller_id = l.seller_id
            AND i.product_id = l.product_id
            WHERE l.seller_id = :id
        """, id=userId)

        return float(rows[0][0]) if rows and rows[0][0] is not None else 0.0


