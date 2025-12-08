from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Optional

from .models.purchase import Purchase
from .models.user import User
from .models.inventory import InventoryItem

from flask import Blueprint
bp = Blueprint('users', __name__)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_auth(form.email.data, form.password.data)
        if user is None:
            flash('Invalid email or password')
            return redirect(url_for('users.login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index.index')

        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


class RegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    address = StringField('Address', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(),
                                       EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        if User.email_exists(email.data):
            raise ValidationError('Already a user with this email. Please choose a different one.')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.register(
            firstname=form.firstname.data,
            lastname=form.lastname.data,
            email=form.email.data,
            password=form.password.data,
            address=form.address.data
        ):
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index.index'))

#PROFILE PAGE
@bp.route('/profile')
def profile():
    # Only logged-in users can see this page
    if current_user.is_authenticated:
        purchases = Purchase.get_all_purchanditems_for_user(current_user.id)
        selling_products = InventoryItem.get_for_seller(current_user.id)
    else:
        flash("Please log in to view your profile.", "warning")
        return redirect(url_for('users.login'))  
    return render_template('userprofile.html', 
                           user=current_user, purchases=purchases,
                           selling_products=selling_products,
                           balance=current_user.balance
                           )

#FORM TO UPDATE PROFILE
class UpdateProfileForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    address = StringField('Address', validators=[Optional()])
    password = PasswordField('New Password', validators=[Optional()])
    password2 = PasswordField('Confirm Password', validators=[Optional(), EqualTo('password')])
    submit = SubmitField('Update Profile')

#PROFILE UPDATE ROUTE
@bp.route('/profile/update', methods=['GET', 'POST'])
def update_profile():
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    form = UpdateProfileForm()

    if request.method == 'GET':
        # Pre-fill form with current info
        form.firstname.data = current_user.firstname
        form.lastname.data = current_user.lastname
        form.email.data = current_user.email
        form.address.data = current_user.address
        return render_template('update_profile.html', form=form) #allows user to see existing info

    if form.validate_on_submit():
        result = User.update(
            user_id=current_user.id,
            email=form.email.data,
            firstname=form.firstname.data,
            lastname=form.lastname.data,
            address=form.address.data,
            password=form.password.data if form.password.data else None
        ) #writes updated info to database

        if result == "email_taken":
            flash("That email is already in use by another account.", "danger")
            return redirect(url_for('users.update_profile'))

        flash("Profile updated!", "success")
        return redirect(url_for('users.profile'))

    return render_template('update_profile.html', form=form)

#topup function
@bp.route('/profile/topup', methods=['POST'])
def topup():
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    amount = request.form.get('amount', type=float)
    if amount<0:
        flash("Please enter a value greater than 0", "danger")
        return redirect(url_for('users.profile'))
    if amount is None:
        flash("Please enter a value", "danger")
        return redirect(url_for('users.profile'))
    
    User.topup(current_user.id, amount)
    flash(f"Successfully topped up ${amount:.2f} to your account.", "success")
    return redirect(url_for('users.profile'))

#withdraw function
@bp.route('/profile/withdraw', methods=['POST'])
def withdraw():
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    amount = request.form.get('amount', type=float)
    if amount<0:
        flash("Please enter a value greater than 0", "danger")
        return redirect(url_for('users.profile'))
    if amount is None:
        flash("Please enter a value", "danger")
        return redirect(url_for('users.profile'))
    #get current balance to make sure withdraw amount doesnt exceed available balance
    if amount > current_user.balance:
        flash("Insufficient funds for this withdrawal.", "danger")
        return redirect(url_for('users.profile'))
    
    User.withdraw(current_user.id, amount)
    flash(f"Successfully withdrew ${amount:.2f} from your account.", "success")
    return redirect(url_for('users.profile'))