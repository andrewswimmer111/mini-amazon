from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from .models.cart import Cart
from .models.purchase import Purchase

bp = Blueprint('cart', __name__)


@bp.route('/cart')
@login_required
def view_cart():
    uid = current_user.id
    items = Cart.format_cart_items(uid)
    total = Cart.get_cart_total(uid)
    count = Cart.get_cart_item_count(uid)
    return render_template('cart.html', items=items, total=total, count=count)


@bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
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

    if sid is None:
        print(f"[add_to_cart] Finding default seller for product {pid}")
        sid = Cart.get_default_seller(pid)
        if sid is None:
            print(f"[add_to_cart] No seller found with inventory for product {pid}")
            if request.is_json:
                return jsonify({'error': 'no seller for product'}), 400
            flash('No seller currently has that product in inventory')
            return redirect(request.referrer or url_for('index.index'))
        print(f"[add_to_cart] Selected default seller {sid} for product {pid}")

    print(f"[add_to_cart] Adding to cart: user={current_user.id}, product={pid}, seller={sid}, qty={qty}")
    Cart.add_item(current_user.id, pid, sid, qty)

    if request.is_json:
        return jsonify({'ok': True})

    flash('Item added to cart')
    return redirect(request.referrer or url_for('index.index'))


@bp.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
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
    address = request.form.get('address', '').strip()
    if not address:
        flash('Please provide a shipping address')
        return redirect(url_for('cart.view_cart'))

    print(f"[purchase] Creating purchase for user {current_user.id} with address: {address}")
    purchase = Purchase.create_from_cart(current_user.id, address)
    
    if not purchase:
        flash('Unable to create purchase - cart may be empty')
        return redirect(url_for('cart.view_cart'))

    flash(f'Purchase completed! Your order ID is {purchase.purchase_id}')
    return redirect(url_for('cart.view_cart'))
