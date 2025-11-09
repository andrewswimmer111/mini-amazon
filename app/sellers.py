# app/sellers.py
from flask import Blueprint, jsonify, render_template, abort, current_app, flash, redirect, url_for, request
from flask_login import login_required, current_user

from .models.inventory import InventoryItem

bp = Blueprint('sellers', __name__, url_prefix='/seller')

@bp.route('/<int:seller_id>/inventory', methods=['GET'])
def seller_inventory_json(seller_id):
    # from app.models.inventory import InventoryItem
    items = InventoryItem.get_for_seller(seller_id)
    return jsonify({
        "seller_id": seller_id,
        "inventory": [i.to_dict() for i in items]
    })

@bp.route('/<int:seller_id>/inventory/view', methods=['GET'])
def seller_inventory_view(seller_id):
    # local imports to avoid circular import issues
    # from app.models.inventory import InventoryItem

    # 1) fetch seller info from DB
    seller_row = current_app.db.execute(
        "SELECT id, email, password, firstname, lastname FROM users WHERE id = :id",
        id=seller_id
    )
    if not seller_row:
        # no such seller/user
        abort(404)

    # seller_row[0] may be a RowProxy/tuple/dict depending on DB.execute return;
    r = seller_row[0]
    # try dictionary-like access first, fallback to tuple indexing
    try:
        seller = {
            "id": r["id"],
            "email": r["email"],
            "firstname": r["firstname"],
            "lastname": r["lastname"],
        }
    except Exception:
        # tuple layout: id, email, password, firstname, lastname
        seller = {
            "id": r[0],
            "email": r[1],
            "firstname": r[3],
            "lastname": r[4],
        }

    # 2) fetch inventory entries
    entries = InventoryItem.get_for_seller(seller_id)

    # 3) pass seller object into template
    return render_template('inventory.html', seller=seller, seller_id=seller_id, entries=entries)


@bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add(product_id):
    InventoryItem.add_or_update(
        seller_id=current_user.id,
        product_id=product_id,
        quantity=request.form.get('quantity', 1)
    )
    flash("Product added to your inventory.")
    return redirect(url_for('items.view_product', product_id=product_id))