# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Username is required.'),
        Length(min=4, max=64, message='Username must be between 4 and 64 characters.')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email or login.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.')
    ])
    submit = SubmitField('Login')

class IncomeForm(FlaskForm):
    amount = FloatField('Amount', validators=[
        DataRequired(message='Amount is required.'),
        NumberRange(min=0.01, message='Amount must be greater than 0.')
    ])
    description = TextAreaField('Description', validators=[
        Length(max=140, message='Description must be less than 140 characters.')
    ])
    submit = SubmitField('Add Income')

class ExpenseForm(FlaskForm):
    raw_text = StringField('Expense Description', validators=[
        DataRequired(message='Expense description is required.'),
        Length(max=140, message='Description must be less than 140 characters.')
    ])
    amount = FloatField('Amount', validators=[
        DataRequired(message='Amount is required.'),
        NumberRange(min=0.01, message='Amount must be greater than 0.')
    ])
    submit = SubmitField('Add Expense')