from flask import render_template
from flask_login import current_user
import datetime


from .models.wishlist import WishlistItem

from flask import Blueprint
bp = Blueprint('wishlist', __name__)

from flask import jsonify
from flask import redirect, url_for
from datetime import datetime, timezone
from flask import request



@bp.route('/wishlist')
def wishlist():
    print("✅ entered wishlist route")  # add this
    if current_user.is_authenticated:
        print("✅ user authenticated")
        items = WishlistItem.get_all_by_uid_since(
            current_user.id, datetime(2000, 9, 14, 0, 0, 0))
        print("✅ finished DB query")
    else:
        return jsonify({}), 404
    print("✅ rendering template")
    return render_template('wishlist.html',
                       items=items,
                       humanize_time=humanize_time)



@bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
def wishlist_add(product_id):
    if current_user.is_authenticated:
        uid = current_user.id
        pid = product_id
        time_added = datetime.now(timezone.utc)

        WishlistItem.Create(uid, pid, time_added)
    return redirect(url_for('wishlist.wishlist'))


from humanize import naturaltime

def humanize_time(dt):
    return naturaltime(datetime.now() - dt)