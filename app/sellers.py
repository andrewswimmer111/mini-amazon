# app/sellers.py
from flask import Blueprint, jsonify, render_template, abort, current_app

bp = Blueprint('sellers', __name__, url_prefix='/seller')

@bp.route('/<int:seller_id>/inventory', methods=['GET'])
def seller_inventory_json(seller_id):
    # local import to avoid circular import / startup import errors
    from app.models.inventory import InventoryItem

    items = InventoryItem.get_for_seller(seller_id)
    return jsonify({
        "seller_id": seller_id,
        "inventory": [i.to_dict() for i in items]
    })

@bp.route('/<int:seller_id>/inventory/view', methods=['GET'])
def seller_inventory_view(seller_id):
    # local import here too
    from app.models.inventory import InventoryItem

    entries = InventoryItem.get_for_seller(seller_id)
    return render_template('inventory.html', seller_id=seller_id, entries=entries)
