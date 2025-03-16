# test_imports.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length

print("All imports succeeded!")
