from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class SelectCityForm(FlaskForm):
    city = StringField('City', validators=[DataRequired()], id='city')
    submit = SubmitField('Get City Data')