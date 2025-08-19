# app.py
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from config import Config
from extensions import db, login_manager
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
import os

# Import transformers and torch for the free LLM solution (if using DialoGPT)
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# # Load DialoGPT model and tokenizer (if you're using the free alternative)
# tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
# dialogue_model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")

# fine_tuned_tokenizer = AutoTokenizer.from_pretrained("./finance_chat_model")
# fine_tuned_model = AutoModelForCausalLM.from_pretrained("./finance_chat_model")

app = Flask(__name__)
app.config.from_object(Config)

# Initialize the extensions with the app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models, ML model, and forms AFTER initializing extensions
from models import User, Income, Expense
from ml_model import predict_category  # if you're using OpenAI-based or any other ML-based prediction
from forms import RegistrationForm, LoginForm, IncomeForm, ExpenseForm

# Create database tables if they do not exist
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/user_finance', methods=['GET'])
@login_required
def user_finance():
    # Get the logged-in user's financial data
    incomes = Income.query.filter_by(user_id=current_user.id).all()
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    
    # Compute totals
    total_income = sum(i.amount for i in incomes)
    total_expense = sum(e.amount for e in expenses)
    balance = total_income - total_expense

    # Build breakdown by category
    categories = {}
    for expense in expenses:
        categories[expense.category] = categories.get(expense.category, 0) + expense.amount

    # Return the data as JSON
    return jsonify({
        "income": total_income,
        "expense": total_expense,
        "balance": balance,
        "categories": categories
    })

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return render_template('register.html', form=form)
        
        # Check if email already exists
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email already registered. Please use a different email or login.', 'danger')
            return render_template('register.html', form=form)
        
        try:
            hashed_pw = generate_password_hash(form.password.data)
            user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in with your new account.', 'success')
            return redirect(url_for('login'))
        except IntegrityError as e:
            db.session.rollback()
            # Handle specific integrity errors
            error_msg = str(e.orig).lower()
            if 'username' in error_msg:
                flash('Username already exists. Please choose a different username.', 'danger')
            elif 'email' in error_msg:
                flash('Email already registered. Please use a different email.', 'danger')
            else:
                flash('Registration failed due to a database error. Please try again.', 'danger')
            return render_template('register.html', form=form)
        except Exception as e:
            db.session.rollback()
            flash('An unexpected error occurred during registration. Please try again.', 'danger')
            return render_template('register.html', form=form)
    
    # If form validation fails, show errors
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field.title()}: {error}', 'danger')
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # First check if user exists by email
        user = User.query.filter_by(email=form.email.data).first()
        
        if not user:
            flash('No account found with this email address. Please check your email or register for a new account.', 'danger')
            return render_template('login.html', form=form)
        
        # Check password
        if check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to next page if specified, otherwise dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Incorrect password. Please check your password and try again.', 'danger')
            return render_template('login.html', form=form)
    
    # If form validation fails, show errors
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field.title()}: {error}', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    flash(f'Goodbye, {username}! You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        incomes = Income.query.filter_by(user_id=current_user.id).all()
        expenses = Expense.query.filter_by(user_id=current_user.id).all()
        total_income = sum(i.amount for i in incomes)
        total_expense = sum(e.amount for e in expenses)
        balance = total_income - total_expense

        # Prepare expense totals by category for charting
        category_totals = {}
        for e in expenses:
            category_totals[e.category] = category_totals.get(e.category, 0) + e.amount

        return render_template('dashboard.html',
                               incomes=incomes,
                               expenses=expenses,
                               total_income=total_income,
                               total_expense=total_expense,
                               balance=balance,
                               category_totals=category_totals)
    except Exception as e:
        flash('Error loading dashboard data. Please try again.', 'danger')
        return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/add_income', methods=['GET', 'POST'])
@login_required
def add_income():
    form = IncomeForm()
    if form.validate_on_submit():
        try:
            income = Income(amount=form.amount.data,
                            description=form.description.data,
                            user_id=current_user.id)
            db.session.add(income)
            db.session.commit()
            flash('Income added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding income. Please try again.', 'danger')
    
    # Show form validation errors
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field.title()}: {error}', 'danger')
    
    return render_template('add_income.html', form=form)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        try:
            # Use ML model to predict expense category
            category = predict_category(form.raw_text.data)
            expense = Expense(raw_text=form.raw_text.data,
                              category=category,
                              amount=form.amount.data,
                              user_id=current_user.id)
            db.session.add(expense)
            db.session.commit()
            flash(f'Expense added successfully! Predicted category: {category}', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding expense. Please try again.', 'danger')
    
    # Show form validation errors
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field.title()}: {error}', 'danger')
    
    return render_template('add_expense.html', form=form)

@app.route('/reset', methods=['POST'])
@login_required
def reset():
    try:
        Income.query.filter_by(user_id=current_user.id).delete()
        Expense.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash('All incomes and expenses have been reset successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error resetting data. Please try again.', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    try:
        expense = Expense.query.get_or_404(expense_id)
        if expense.user_id != current_user.id:
            flash('You do not have permission to delete this expense.', 'danger')
            return redirect(url_for('dashboard'))
        
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting expense. Please try again.', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/api/predict', methods=['POST'])
def api_predict():
    try:
        data = request.get_json(force=True)
        raw_text = data.get('raw_text')
        if not raw_text:
            return jsonify({'error': 'No raw_text provided'}), 400
        
        category = predict_category(raw_text)
        return jsonify({'predicted_category': category})
    except Exception as e:
        return jsonify({'error': 'Prediction failed'}), 500

# Custom error handlers
@app.errorhandler(404)
def not_found_error(error):
    flash('Page not found.', 'danger')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    flash('An internal error occurred. Please try again.', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)