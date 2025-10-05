from flask import Blueprint, jsonify, redirect, url_for
from flask_login import current_user, login_required
from .models.wishlist import WishlistItem

bp = Blueprint('wishlist', __name__)

@bp.route('/wishlist')
@login_required
def wishlist():
    items = WishlistItem.for_user(current_user.id)
    return jsonify([item.__dict__ for item in items])

@bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def wishlist_add(product_id):
    WishlistItem.add(current_user.id, product_id)
    return redirect(url_for('wishlist.wishlist'))
