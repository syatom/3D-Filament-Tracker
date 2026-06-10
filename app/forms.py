"""WTForms for the application"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SubmitField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, NumberRange, Regexp
from app.models import User


class LoginForm(FlaskForm):
    """User login form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class RegisterForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        """Check if username already exists"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """Check if email already exists"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered. Please use a different one.')


class FilamentForm(FlaskForm):
    """Form for adding or editing filament"""
    type = StringField('Filament Type', validators=[
        DataRequired(),
        Length(max=100, message='Type must be less than 100 characters')
    ], description='e.g., PLA Matte, PLA Basic, PETG, ABS')
    
    color = StringField('Color', validators=[
        DataRequired(),
        Length(max=50, message='Color must be less than 50 characters')
    ], description='e.g., Red, Blue, Black, White')
    
    color_hex = StringField('Color Code', validators=[
        DataRequired(),
        Regexp(r'^#[0-9A-Fa-f]{6}$', message='Must be a valid hex color code (e.g., #FF0000)')
    ], default='#808080', description='Visual color representation')
    
    starting_weight = FloatField('Starting Weight (grams)', validators=[
        DataRequired(),
        NumberRange(min=1, message='Weight must be greater than 0')
    ], description='Typical spool: 1000g')
    
    submit = SubmitField('Save Filament')


class UsageForm(FlaskForm):
    """Form for recording filament usage"""
    weight_used = FloatField('Weight Used (grams)', validators=[
        DataRequired(),
        NumberRange(min=0.1, message='Weight must be greater than 0')
    ])
    
    print_name = StringField('Print Name', validators=[
        DataRequired(),
        Length(max=200, message='Print name must be less than 200 characters')
    ], description='Name or description of the print job')
    
    component_name = StringField('Component Name', validators=[
        DataRequired(),
        Length(max=200, message='Component name must be less than 200 characters')
    ], description='Name of the printed part or component')
    
    submit = SubmitField('Record Usage')


class LinkNewSpoolForm(FlaskForm):
    """Form for linking a new spool when usage exceeds remaining weight"""
    type = StringField('Filament Type', validators=[
        DataRequired(),
        Length(max=100)
    ])
    
    color = StringField('Color', validators=[
        DataRequired(),
        Length(max=50)
    ])
    
    starting_weight = FloatField('Starting Weight (grams)', validators=[
        DataRequired(),
        NumberRange(min=1)
    ])
    
    submit = SubmitField('Add New Spool')


class MulticolorUsageForm(FlaskForm):
    """Form for recording multicolor (AMS) print usage across multiple filaments"""
    print_name = StringField('Print Name', validators=[
        DataRequired(),
        Length(max=200, message='Print name must be less than 200 characters')
    ], description='Name or description of the multicolor print job')
    
    component_name = StringField('Component Name', validators=[
        DataRequired(),
        Length(max=200, message='Component name must be less than 200 characters')
    ], description='Name of the printed part or component')
    
    submit = SubmitField('Record Multicolor Print')

