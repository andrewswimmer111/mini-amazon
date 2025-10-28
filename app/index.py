from flask import render_template
from flask_login import current_user
import datetime

from .models.product import Product
from .models.purchase import Purchase

from flask import Blueprint, request
bp = Blueprint('index', __name__)

@bp.route('/test')
def test():
    print("test route called!!!")
    return "Hello world"


@bp.route('/')
def index():

    top_k = request.args.get('top_k', type=int)
    products = Product.get_k_most_expensive(top_k) if top_k else Product.get_all()
    total_products = len(Product.get_all())


    return render_template('index.html',
                           avail_products=products,
                           k=top_k,
                           n=total_products)
