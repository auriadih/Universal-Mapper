# import custom forms libraries
from flask_wtf import FlaskForm

# import classes for form field types
from wtforms import PasswordField, StringField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo

# import db query class to 'user' table
from ..models import User



# define registration form
class RegistrationForm(FlaskForm):

    # all field are required
    email = StringField('Email', validators = [DataRequired(), Email()])
    organisation = StringField('Organisaatio', validators = [DataRequired()])
    username = StringField('Käyttäjätunnus', validators = [DataRequired()])
    first_name = StringField('Etunimi', validators = [DataRequired()])
    last_name = StringField('Sukunimi', validators = [DataRequired()])
    password = PasswordField('Salasana', validators = [DataRequired(), EqualTo('confirm_password')])
    confirm_password = PasswordField('Varmista salasana')
    submit = SubmitField('Rekisteröidy')

	# check if email is already registered
    def validate_email(self, field):
        if User.query.filter_by(email = field.data).first():
            raise ValidationError('Tämä sähköpostiosoite on jo rekisteröity käyttäjätunnukselle.')

	# check if username is already registered
    def validate_username(self, field):
        if User.query.filter_by(username = field.data).first():
            raise ValidationError('Tämä käyttäjätunnus on jo käytössä.')



# define login form
class LoginForm(FlaskForm):
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Salasana', validators = [DataRequired()])
    submit = SubmitField('Kirjaudu sisään')
