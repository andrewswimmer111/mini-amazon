from flask import render_template
from flask_login import current_user
import datetime

from .models.product import Product
from .models.purchase import Purchase

from flask import Blueprint, request
bp = Blueprint('index', __name__)


@bp.route('/')
def index():

    top_k = request.args.get('top_k', type=int)
    products = Product.get_k_most_expensive(top_k) if top_k else Product.get_all()
    total_products = len(Product.get_all())

    # find the products current user has bought:
    if current_user.is_authenticated:
        purchases = Purchase.get_all_by_uid_since(
            current_user.id, datetime.datetime(1980, 9, 14, 0, 0, 0))
    else:
        purchases = None
    # render the page by adding information to the index.html file

    return render_template('index.html',
                           avail_products=products,
                           purchase_history=purchases,
                           k=top_k,
                           n=total_products)
