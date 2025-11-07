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

    # Settings
    PER_PAGE = 5

    # Params
    category = request.args.get('category', type=str) or None
    keyword = request.args.get('keyword', type=str) or None
    minPrice = request.args.get('minPrice', type=float) or None
    maxPrice = request.args.get('maxPrice', type=float) or None

    sortBy = request.args.get('sortBy', "price", type=str)
    sortDir = request.args.get('sortDir', "asc", type=str)

    limit = request.args.get('limit', type=int) or None

    products = Product.get_with_filters(category, keyword, minPrice, maxPrice, sortBy, sortDir, limit)
    total_products = len(Product.get_all())

    categories = Product.get_categories()

    return render_template('index.html',
                            avail_products=products,
                            n=total_products,
                            categories=categories,
                            selected_category=category,
                            keyword=keyword,
                            minPrice=minPrice,
                            maxPrice=maxPrice,
                            sortBy=sortBy,
                            sortDir=sortDir,
                            limit=limit)
