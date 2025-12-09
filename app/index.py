from math import ceil

from flask import render_template
from flask_login import current_user
import datetime

from .models.product import Product

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

    sortBy = request.args.get('sortBy', "name", type=str)
    sortDir = request.args.get('sortDir', "asc", type=str)

    # Pagination
    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1
    
    offset = (page - 1) * PER_PAGE
    total = Product.count_with_filters(category=category, keyword=keyword)
    pages = ceil(total / PER_PAGE)

    # Calculate products and categories
    products = Product.get_with_filters(category, keyword, sortBy, sortDir, PER_PAGE, offset)
    categories = Product.get_categories()


    if request.headers.get('HX-Request'):  # HTMX request
        return render_template('_products_fragment.html', 
                               avail_products=products,
                               page=page, pages=pages, total=total)
    else:
        return render_template('index.html', 
                               avail_products=products, page=page,
                               pages=pages, total=total,
                               categories=categories, selected_category=category,
                               keyword=keyword,
                               sortBy=sortBy, sortDir=sortDir)
