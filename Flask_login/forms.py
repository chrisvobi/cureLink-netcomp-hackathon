from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
import mysql.connector
from db import get_db_connection

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    zip_code = StringField('Zip Code', validators=[DataRequired(), Length(min=5, max=5)])
    street = StringField('Street', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM patients WHERE email = %s", (email.data,))
        patient = cursor.fetchone()
        connection.close()
        if patient:
            raise ValidationError('That email is already registered. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
