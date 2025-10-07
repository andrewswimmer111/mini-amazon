# app/wishlist.py
from flask import Blueprint, render_template, jsonify, redirect, url_for, request, flash
from flask_login import current_user, login_required
from app.models.wishlist import WishlistItem
import datetime

bp = Blueprint('wishlist', __name__)

@bp.route('/wishlist')
@login_required
def wishlist():
    uid = current_user.id if hasattr(current_user, 'id') else current_user.uid
    items = WishlistItem.get_for_user(uid)
    # helper to humanize times in template (requires humanize package installed)
    from humanize import naturaltime
    def humanize_time(dt):
        return naturaltime(datetime.datetime.utcnow() - dt)
    return render_template('wishlist.html', items=items, humanize_time=humanize_time)

@bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def wishlist_add(product_id):
    uid = current_user.id if hasattr(current_user, 'id') else current_user.uid
    # Optionally avoid duplicates
    if not WishlistItem.exists(uid, product_id):
        WishlistItem.add(uid, product_id)
        flash('Added to wishlist.', 'success')
    else:
        flash('Already on wishlist.', 'info')
    return redirect(url_for('wishlist.wishlist'))
