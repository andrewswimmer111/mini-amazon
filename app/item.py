
from flask_login import current_user
from flask import Blueprint, request, render_template

from .models.product import Product
from .models.inventory import InventoryItem

bp = Blueprint('items', __name__)

@bp.route('/product/<int:product_id>')
def view_product(product_id):
    product = Product.get_with_id(product_id)
    inventory = InventoryItem.get_sellers_from_product(product_id)
    return render_template('product_detail.html', 
                           product=product, inventory=inventory
                           )