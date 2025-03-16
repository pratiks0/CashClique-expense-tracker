# app.py
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from config import Config
from extensions import db, login_manager
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Import transformers and torch for the free LLM solution (if using DialoGPT)
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Load DialoGPT model and tokenizer (if you're using the free alternative)
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
dialogue_model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")

fine_tuned_tokenizer = AutoTokenizer.from_pretrained("./finance_chat_model")
fine_tuned_model = AutoModelForCausalLM.from_pretrained("./finance_chat_model")

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
        hashed_pw = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Check email and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
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

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/add_income', methods=['GET', 'POST'])
@login_required
def add_income():
    form = IncomeForm()
    if form.validate_on_submit():
        income = Income(amount=form.amount.data,
                        description=form.description.data,
                        user_id=current_user.id)
        db.session.add(income)
        db.session.commit()
        flash('Income added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_income.html', form=form)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        # Use ML model to predict expense category
        category = predict_category(form.raw_text.data)
        expense = Expense(raw_text=form.raw_text.data,
                          category=category,
                          amount=form.amount.data,
                          user_id=current_user.id)
        db.session.add(expense)
        db.session.commit()
        flash(f'Expense added! Predicted category: {category}', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_expense.html', form=form)

@app.route('/reset', methods=['POST'])
@login_required
def reset():
    Income.query.filter_by(user_id=current_user.id).delete()
    Expense.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('All incomes and expenses have been reset.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user.id:
        flash('You do not have permission to delete this expense.', 'danger')
        return redirect(url_for('dashboard'))
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.get_json(force=True)
    raw_text = data.get('raw_text')
    if not raw_text:
        return jsonify({'error': 'No raw_text provided'}), 400
    category = predict_category(raw_text)
    return jsonify({'predicted_category': category})

if __name__ == '__main__':
    app.run(debug=True)