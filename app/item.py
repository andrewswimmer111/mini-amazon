
from flask_login import current_user, login_required
from flask import Blueprint, request, render_template, flash, redirect, url_for, abort

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DecimalField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange, Optional

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


class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    image = StringField('Image URL', validators=[Optional()])
    category = SelectField('Category', validators=[DataRequired()], coerce=str)
    created_by = IntegerField('Created By (User ID)', validators=[Optional()])
    submit = SubmitField('Create Product')

@bp.route('/create_product', methods=['GET', 'POST'])
@login_required
def create_product():
    categories = Product.get_categories() 
    form = ProductForm()

    # populate select choices as (value,label) tuples
    form.category.choices = [(str(c), c) for c in categories]

    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        image = form.image.data or None
        category = form.category.data
        created_by = form.created_by.data or current_user.id if current_user.is_authenticated else None

        try:
            product = Product.create(
                name=name,
                description=description,
                image=image,
                category=category,
                created_by=created_by
            )
        except Exception as e:
            flash('Could not create product: ' + str(e), 'danger')
            return render_template('create_product.html', form=form)

        return redirect(url_for('items.view_product', product_id=product.id))

    return render_template('create_product.html', form=form)


@bp.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):

    uid = current_user.id
    if product.created_by != current_user.id:
        abort(403)

    product = Product.get_with_id(product_id)
    
    # Check creation (not implemented in db yet)
    # if product.created_by != uid:
    #     return

    categories = Product.get_categories()
    form = ProductForm(obj=product)
    form.category.choices = [(str(c), c) for c in categories]

    if form.validate_on_submit():
        # Pull values from the form
        product.name = form.name.data
        product.description = form.description.data
        product.image = form.image.data or None
        product.category = form.category.data
        created_by = form.created_by.data if form.created_by.data else product.created_by

        try:
            product = Product.update(product_id,
                                     name=product.name,
                                     description=product.description,
                                     image=product.image,
                                     category=product.category,
                                     created_by=created_by)
        except Exception as e:
            flash('Could not update product: ' + str(e), 'danger')
            return render_template('create_product.html', form=form, edit=True)

        return redirect(url_for('items.view_product', product_id=product_id))

    return render_template('create_product.html', form=form, edit=True)