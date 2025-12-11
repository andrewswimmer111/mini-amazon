"""Routes for viewing and modifying the user's shopping cart.

This module provides endpoints to view the cart, add/update/remove
items, and to create purchases from the current cart contents.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from .models.cart import Cart
from .models.purchase import Purchase
from .models.user import User

bp = Blueprint('cart', __name__)


@bp.route('/cart')
@login_required
def view_cart():
    """Render the current user's cart page.

    Aggregates formatted items, totals and user balance for rendering.
    """
    uid = current_user.id
    items = Cart.format_cart_items(uid)
    total = Cart.get_cart_total(uid)
    count = Cart.get_cart_item_count(uid)
    balance = current_user.balance
    return render_template('cart.html', items=items, total=total, count=count, balance=balance)


@bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    """Add a product to the current user's cart.

    Accepts JSON or form data with `product_id`, optional `seller_id`,
    and optional `quantity`. If `seller_id` is omitted, a default seller
    is selected from inventory.
    """

    data = request.get_json(silent=True) or request.form
    try:
        pid = int(data.get('product_id'))
        sid_raw = data.get('seller_id')
        sid = None if sid_raw in (None, '') else int(sid_raw)
        qty = int(data.get('quantity', 1))
    except (TypeError, ValueError):
        if request.is_json:
            return jsonify({'error': 'invalid parameters'}), 400
        flash('Invalid add-to-cart parameters')
        return redirect(request.referrer or url_for('index.index'))

    # If no seller provided, choose a default seller with inventory.
    if sid is None:
        sid = Cart.get_default_seller(pid)
        if sid is None:
            # No available seller for this product.
            if request.is_json:
                return jsonify({'error': 'no seller for product'}), 400
            flash('No seller currently has that product in inventory')
            return redirect(request.referrer or url_for('index.index'))

    # Persist the cart change.
    Cart.add_item(current_user.id, pid, sid, qty)

    if request.is_json:
        return jsonify({'ok': True})

    flash('Item added to cart')
    return redirect(request.referrer or url_for('index.index'))


@bp.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    """Update the quantity of an item already in the cart."""

    data = request.get_json(silent=True) or request.form
    try:
        pid = int(data.get('product_id'))
        sid = int(data.get('seller_id'))
        qty = int(data.get('quantity'))
    except (TypeError, ValueError):
        if request.is_json:
            return jsonify({'error': 'invalid parameters'}), 400
        flash('Invalid update parameters')
        return redirect(request.referrer or url_for('cart.view_cart'))

    result = Cart.update_item(current_user.id, pid, sid, qty)

    if request.is_json:
        return jsonify({'ok': True, 'quantity': result})

    flash('Cart updated')
    return redirect(request.referrer or url_for('cart.view_cart'))


@bp.route('/cart/remove', methods=['POST'])
@login_required
def remove_from_cart():
    """Remove an item from the current user's cart."""

    data = request.get_json(silent=True) or request.form
    try:
        pid = int(data.get('product_id'))
        sid = int(data.get('seller_id'))
    except (TypeError, ValueError):
        if request.is_json:
            return jsonify({'error': 'invalid parameters'}), 400
        flash('Invalid remove parameters')
        return redirect(request.referrer or url_for('cart.view_cart'))

    deleted = Cart.remove_item(current_user.id, pid, sid)

    if request.is_json:
        return jsonify({'ok': bool(deleted)})

    flash('Item removed from cart' if deleted else 'Item not found in cart')
    return redirect(request.referrer or url_for('cart.view_cart'))


@bp.route('/cart/purchase', methods=['POST'])
@login_required
def purchase():
    """Create a purchase from the user's cart and clear it on success.

    Requires a non-empty `address` form field. Handles low-balance
    and empty-cart cases returned by the purchase helper.
    """

    address = request.form.get('address', '').strip()
    if not address:
        flash('Please provide a shipping address')
        return redirect(url_for('cart.view_cart'))

    purchase = Purchase.create_from_cart(current_user.id, address)
    
    if purchase is None:
        flash('Unable to create purchase - cart may be empty or insufficient balance', 'error')
        return redirect(url_for('cart.view_cart'))
    
    if purchase == 'insufficient_balance':
        flash('Insufficient balance to complete purchase. Please add funds to your account.', 'error')
        return redirect(url_for('cart.view_cart'))

    flash(f'Purchase completed! Your order ID is {purchase.purchase_id}')
    return redirect(url_for('cart.view_cart'))
