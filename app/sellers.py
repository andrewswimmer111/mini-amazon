# app/sellers.py
from flask import Blueprint, jsonify, render_template, abort, current_app, flash, redirect, url_for, request
from flask_login import login_required, current_user

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
    
    if not product_id:
        flash("Please select a product to add.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    if quantity <= 0:
        flash("Quantity must be greater than 0.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    # Check if product exists
    product = Product.get_with_id(product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    result = InventoryItem.add_or_update(current_user.id, product_id, quantity)
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
    category = request.form.get('category', '').strip()
    quantity = request.form.get('quantity', 1, type=int)
    
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
    
    if not category:
        flash("Please select a category.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    if quantity <= 0:
        flash("Quantity must be greater than 0.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    # Create the product
    product = Product.create(name=name, description=description, price=price, category=category)
    if not product:
        flash("Failed to create product. The name might already exist.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    # Add to inventory
    result = InventoryItem.add_or_update(current_user.id, product.id, quantity)
    if result:
        flash(f"Created '{name}' and added {quantity} units to your inventory.", "success")
    else:
        flash(f"Product '{name}' created but failed to add to inventory.", "warning")
    
    return redirect(url_for('sellers.my_inventory'))


@bp.route('/inventory/update-price/<int:product_id>', methods=['POST'])
@login_required
def update_product_price(product_id):
    """Update the price of a product."""
    price = request.form.get('price', type=float)
    
    if price is None or price < 0:
        flash("Please enter a valid price.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    # Check if user has this product in their inventory
    item = InventoryItem.get_item(current_user.id, product_id)
    if not item:
        flash("You can only update prices for products in your inventory.", "danger")
        return redirect(url_for('sellers.my_inventory'))
    
    result = Product.update_price(product_id, price)
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


@bp.route('/<int:seller_id>/inventory/view', methods=['GET'])
def seller_inventory_view(seller_id):
    """View a seller's inventory (public view)."""
    seller = User.get(seller_id)
    if not seller:
        abort(404)

    entries = InventoryItem.get_for_seller(seller_id)
    return render_template('inventory.html', 
                           seller=seller, 
                           seller_id=seller_id, 
                           entries=entries)


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY ROUTE (for adding from product detail page)
# ─────────────────────────────────────────────────────────────────────────────

@bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add(product_id):
    """Add a product to inventory from product detail page."""
    quantity = request.form.get('quantity', 1, type=int)
    InventoryItem.add_or_update(
        seller_id=current_user.id,
        product_id=product_id,
        quantity=quantity
    )
    flash("Product added to your inventory.", "success")
    return redirect(url_for('items.view_product', product_id=product_id))