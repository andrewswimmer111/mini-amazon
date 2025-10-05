from flask import render_template
from flask_login import current_user
import datetime

from .models.product import Product
from .models.wishlist import WishlistItem

from flask import Blueprint
bp = Blueprint('wishlist', __name__)

from flask import jsonify
from flask import redirect, url_for
from datetime import datetime, timezone



@bp.route('/wishlist')
def wishlist():
    # find the products on current user wishlist:
    if current_user.is_authenticated:
        items = WishlistItem.get_all_by_uid_since(
            current_user.id, datetime(1900, 9, 14, 0, 0, 0))
    else:
        return jsonify({}), 404
    # render the page by adding information to the index.html file
    return jsonify([item.__dict__ for item in items])

@bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
def wishlist_add(product_id):
    if current_user.is_authenticated:
        uid = current_user.id
        pid = product_id
        time_added = datetime.now(timezone.utc)

        WishlistItem.Create(uid, pid, time_added)
    return redirect(url_for('wishlist.wishlist'))


