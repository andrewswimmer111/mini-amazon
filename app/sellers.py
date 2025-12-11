# app/sellers.py
from flask import Blueprint, jsonify, render_template, abort, flash, redirect, url_for, request
from flask_login import login_required, current_user
from flask import current_app as app
from math import ceil

from .models.inventory import InventoryItem
from .models.product import Product
from .models.user import User



bp = Blueprint('sellers', __name__, url_prefix='/seller')


# ─────────────────────────────────────────────────────────────────────────────
# MY INVENTORY - Main page for seller to manage their inventory
# ─────────────────────────────────────────────────────────────────────────────

@bp.route('/inventory', methods=['GET'])
@login_required
def my_inventory():
    """Display the current user's inventory with management options."""
    entries = InventoryItem.get_for_seller(current_user.id)
    available_products = InventoryItem.get_products_not_in_inventory(current_user.id)
    categories = Product.get_categories()
    
    return render_template(
        'seller_inventory.html',
        entries=entries,
        available_products=available_products,
        categories=categories
    )


@bp.route('/inventory/add', methods=['POST'])
@login_required
def add_to_inventory():
    """Add a product to seller's inventory."""
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)
    price = request.form.get('price', type=float)
    
    if not product_id:
        flash("Please select a product to add.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    if quantity <= 0:
        flash("Quantity must be greater than 0.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    if price is None or price < 0:
        flash("Please enter a valid price.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    # Check if product exists
    product = Product.get_with_id(product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    result = InventoryItem.add_or_update(current_user.id, product_id, quantity, price)
    if result:
        flash(f"Added {quantity} units of '{product.name}' to your inventory.", "success")
    else:
        flash("Failed to add product to inventory.", "danger")
    
    return redirect(url_for('sellers.my_inventory'))


@bp.route('/inventory/create-product', methods=['POST'])
@login_required
def create_product_and_add():
    """Create a new product and add it to seller's inventory."""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    price = request.form.get('price', type=float)
    image = request.form.get('image', '').strip()
    category = request.form.get('category', '').strip()
    quantity = request.form.get('quantity', 1, type=int)
    created_by = current_user.id
    
    # Validation
    if not name:
        flash("Product name is required.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    if not description:
        flash("Product description is required.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    if price is None or price < 0:
        flash("Please enter a valid price.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    if not image: 
        flash("Image is required.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    if not category:
        flash("Please select a category.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    if quantity <= 0:
        flash("Quantity must be greater than 0.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    # Create the product
    product = Product.create(name=name, description=description, category=category, image=image, created_by=created_by)
    if not product:
        flash("Failed to create product. The name might already exist.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    # Add to inventory with price
    result = InventoryItem.add_or_update(current_user.id, product.id, quantity, price)
    if result:
        flash(f"Created '{name}' and added {quantity} units to your inventory.", "success")
    else:
        flash(f"Product '{name}' created but failed to add to inventory.", "warning")
    
    return redirect(url_for('sellers.my_inventory'))


@bp.route('/inventory/update-price/<int:product_id>', methods=['POST'])
@login_required
def update_product_price(product_id):
    """Update the price of a product in inventory."""
    price = request.form.get('price', type=float)
    
    if price is None or price < 0:
        flash("Please enter a valid price.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    # Check if user has this product in their inventory
    item = InventoryItem.get_item(current_user.id, product_id)
    if not item:
        flash("You can only update prices for products in your inventory.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    # Update price in inventory
    result = InventoryItem.set_quantity(current_user.id, product_id, item.quantity, price)
    if result:
        flash(f"Price updated to ${price:.2f}.", "success")
    else:
        flash("Failed to update price.", "danger")
    
    return redirect(url_for('sellers.my_inventory'))


@bp.route('/inventory/update/<int:product_id>', methods=['POST'])
@login_required
def update_inventory_quantity(product_id):
    """Update the quantity of a product in seller's inventory."""
    quantity = request.form.get('quantity', type=int)
    
    if quantity is None:
        flash("Please enter a valid quantity.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    if quantity <= 0:
        # If quantity is 0 or less, remove the item
        result = InventoryItem.remove_from_inventory(current_user.id, product_id)
        if result:
            flash("Product removed from your inventory.", "success")
        else:
            flash("Failed to remove product from inventory.", "danger")
    else:
        result = InventoryItem.set_quantity(current_user.id, product_id, quantity)
        if result:
            flash("Inventory quantity updated.", "success")
        else:
            flash("Failed to update inventory quantity.", "danger")
    
    return redirect(url_for('sellers.my_inventory'))


@bp.route('/inventory/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_inventory(product_id):
    """Remove a product from seller's inventory entirely."""
    result = InventoryItem.remove_from_inventory(current_user.id, product_id)
    if result:
        flash("Product removed from your inventory.", "success")
    else:
        flash("Failed to remove product from inventory.", "danger")
    
    return redirect(url_for('sellers.my_inventory'))


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC SELLER VIEW 
# ─────────────────────────────────────────────────────────────────────────────

@bp.route('/<int:seller_id>/inventory', methods=['GET'])
def seller_inventory_json(seller_id):
    """Get seller's inventory as JSON."""
    items = InventoryItem.get_for_seller(seller_id)
    return jsonify({
        "seller_id": seller_id,
        "inventory": [i.to_dict() for i in items]
    })


@bp.route('/<int:seller_id>/inventory/view')
def seller_inventory_view(seller_id):

    PER_PAGE = 10 

    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1

    offset = (page - 1) * PER_PAGE

    seller = User.get(seller_id)
    if not seller:
        return render_template("seller_not_found.html", seller_id=seller_id), 404

    # Count number of products this seller has
    total = app.db.execute(
        "SELECT COUNT(*) FROM Inventory WHERE seller_id = :id",
        id=seller_id
    )[0][0]

    pages = ceil(total / PER_PAGE) if total else 1

    # Fetch only paginated entries
    entries = app.db.execute("""
        SELECT i.seller_id, i.product_id, i.quantity, i.price,
               p.name, p.category, p.image
        FROM Inventory i
        LEFT JOIN Products p ON p.id = i.product_id
        WHERE i.seller_id = :seller_id
        ORDER BY p.name
        LIMIT :limit OFFSET :offset
    """, seller_id=seller_id, limit=PER_PAGE, offset=offset)

    entries = [InventoryItem.from_row(row) for row in entries]

    return render_template(
        "inventory.html",
        seller=seller,
        seller_id=seller_id,
        entries=entries,
        page=page,
        pages=pages,
        total=total
    )


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY ROUTE (for adding from product detail page)
# ─────────────────────────────────────────────────────────────────────────────

@bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add(product_id):
    """Add a product to inventory from product detail page."""
    quantity = request.form.get('quantity', 1, type=int)
    price = request.form.get('price', type=float)
    
    if price is None or price < 0:
        flash("Please enter a valid price.", "danger")
        return redirect(url_for('items.view_product', product_id=product_id))
    
    InventoryItem.add_or_update(
        seller_id=current_user.id,
        product_id=product_id,
        quantity=quantity,
        price=price
    )
    flash("Product added to your inventory.", "success")
    return redirect(url_for('items.view_product', product_id=product_id))

# ─────────────────────────────────────────────────────────────────────────────
# SELLER ORDER HISTORY / FULFILLMENT (using Purchases + Ledger)
# ─────────────────────────────────────────────────────────────────────────────

@bp.route('/orders', methods=['GET'])
@login_required
def seller_orders():
    """
    Show this seller's orders (each row is a line item),
    sorted reverse‑chronologically.
    Uses Purchases + Ledger + Users (+ Inventory for current price).
    """
    seller_id = current_user.id

    status_filter = request.args.get('status', 'all')  # 'incomplete' | 'complete' | 'all'
    search = request.args.get('q', '').strip().lower()

    # Pull all line items for this seller, newest purchases first.
    # NOTE: schema from your create.sql:
    #   Purchases(purchase_id, address, date, buyer_id, fulfillment_status)
    #   Ledger(purchase_id, seller_id, product_id, quantity, fulfillment_status)
    #   Users(id, firstname, lastname, address, ...)
    #   Inventory(seller_id, product_id, price, ...)
    rows = app.db.execute(
        """
        SELECT
            p.purchase_id                    AS order_id,
            l.product_id,
            u.firstname,
            u.lastname,
            p.address                        AS buyer_address,
            l.quantity,
            COALESCE(i.price, 0) * l.quantity AS payment_amount,
            p.date                           AS time_purchased,
            l.fulfillment_status
        FROM Purchases p
        JOIN Ledger l
          ON l.purchase_id = p.purchase_id
        JOIN Users u
          ON u.id = p.buyer_id
        LEFT JOIN Inventory i
          ON i.seller_id = l.seller_id
         AND i.product_id = l.product_id
        WHERE l.seller_id = :seller_id
        ORDER BY p.date DESC
        """,
        seller_id=seller_id,
    )

    transactions = []
    for row in rows:
        status_int = row[8]  # l.fulfillment_status
        status_str = "Complete" if status_int == 1 else "Pending"

        t = {
            "order_id": row[0],
            "product_id": row[1],
            "buyer_name": f"{row[2]} {row[3]}",
            "address": row[4],
            "quantity": int(row[5]),
            "payment_amount": float(row[6]),  # may be 0 if no Inventory row
            "time_purchased": row[7],
            "status": status_str,
        }
        transactions.append(t)

    # Filter by status
    if status_filter == "incomplete":
        transactions = [t for t in transactions if t["status"] != "Complete"]
    elif status_filter == "complete":
        transactions = [t for t in transactions if t["status"] == "Complete"]
    # 'all' → no extra filtering

    # Simple text search (order id, product id, buyer, address)
    if search:
        search_lc = search.lower()
        filtered = []
        for t in transactions:
            if (
                search_lc in str(t["order_id"]).lower()
                or search_lc in str(t["product_id"]).lower()
                or search_lc in t["buyer_name"].lower()
                or search_lc in (t["address"] or "").lower()
            ):
                filtered.append(t)
        transactions = filtered

    # Counts for summary badges
    pending_count = app.db.execute(
        """
        SELECT COUNT(*)
        FROM Ledger
        WHERE seller_id = :seller_id AND fulfillment_status = 0
        """,
        seller_id=seller_id,
    )[0][0]

    complete_count = app.db.execute(
        """
        SELECT COUNT(*)
        FROM Ledger
        WHERE seller_id = :seller_id AND fulfillment_status = 1
        """,
        seller_id=seller_id,
    )[0][0]

    return render_template(
        "seller_orders.html",
        transactions=transactions,
        status_filter=status_filter,
        search=search,
        pending_count=pending_count,
        complete_count=complete_count,
    )


@bp.route('/orders/<int:order_id>/product/<int:product_id>/fulfill', methods=['POST'])
@login_required
def mark_line_item_fulfilled(order_id, product_id):
    """
    Mark a single line item as fulfilled for the current seller.
    Uses Ledger.fulfillment_status.
    Does NOT touch Inventory (stock was updated at purchase time).
    """
    seller_id = current_user.id

    rows = app.db.execute(
        """
        UPDATE Ledger
        SET fulfillment_status = 1
        WHERE purchase_id       = :purchase_id
          AND product_id        = :product_id
          AND seller_id         = :seller_id
          AND fulfillment_status = 0
        RETURNING purchase_id
        """,
        purchase_id=order_id,
        product_id=product_id,
        seller_id=seller_id,
    )

    if rows:
        flash(f"Marked order #{order_id}, product {product_id} as fulfilled.", "success")
        purchase_id = rows[0][0]

        # OPTIONAL: If you want to also update Purchases.fulfillment_status once
        # all items are fulfilled, you can uncomment this block:
        #
        # app.db.execute(
        #     """
        #     UPDATE Purchases
        #     SET fulfillment_status = 1
        #     WHERE purchase_id = :purchase_id
        #       AND NOT EXISTS (
        #           SELECT 1 FROM Ledger
        #           WHERE purchase_id = :purchase_id
        #             AND fulfillment_status = 0
        #       )
        #     """,
        #     purchase_id=purchase_id,
        # )
    else:
        flash(
            "Could not mark this line item as fulfilled. "
            "It may already be complete or may not belong to you.",
            "warning",
        )

    return redirect(request.referrer or url_for('sellers.seller_orders'))

@bp.route('/orders/<int:order_id>/product/<int:product_id>/unfulfill', methods=['POST'])
@login_required
def mark_line_item_unfulfilled(order_id, product_id):
    """
    Reverse fulfillment for a single line item.
    Marks Ledger.fulfillment_status back to 0.
    """
    seller_id = current_user.id

    rows = app.db.execute(
        """
        UPDATE Ledger
        SET fulfillment_status = 0
        WHERE purchase_id       = :purchase_id
          AND product_id        = :product_id
          AND seller_id         = :seller_id
          AND fulfillment_status = 1
        RETURNING purchase_id
        """,
        purchase_id=order_id,
        product_id=product_id,
        seller_id=seller_id,
    )

    if rows:
        flash(f"Marked order #{order_id}, product {product_id} as UNFULFILLED.", "warning")
    else:
        flash(
            "Could not reverse fulfillment. "
            "Item may already be pending or may not belong to you.",
            "danger"
        )

    return redirect(request.referrer or url_for('sellers.seller_orders'))
