from flask import render_template
from flask_login import current_user
import datetime

from .models.product import Product
from .models.purchase import Purchase
from .models.wishlist import WishlistItem

from flask import Blueprint

from flask import jsonify
from flask import redirect, url_for
from humanize import naturaltime


bp = Blueprint('wishlist', __name__)

@bp.route('/wishlist')

def wishlist():
    if not current_user.is_authenticated:
        return jsonfiy({}), 404
    items = WishlistItem.get_all_by_uid_since(
            current_user.id, datetime.datetime(1980, 9, 14, 0, 0, 0))

    return render_template('wishlist.html',
                            items=items,
                            humanize_time=humanize_time)


@bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
def wishlist_add(product_id):
    if not current_user.is_authenticated:
        return jsonify({}), 404
    x = WishlistItem.create(
        current_user.id, product_id, datetime.datetime.utcnow()
    )
    return redirect(url_for('wishlist.wishlist'))

def humanize_time(dt):
    return naturaltime(datetime.datetime.now() - dt)
    
    