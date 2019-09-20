from flask import Flask, render_template, request, g, flash, redirect, url_for
import openaq
from .models import DB, Record
from .forms import SelectCityForm


def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    app.secret_key = 'super secret key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    DB.init_app(app)

    # Create route to the home page
    @app.route('/')
    def root():
        #data = fetch_data()
        return render_template(
            'base.html', title='Home', form=SelectCityForm())

    @app.route('/run', methods=(['GET', 'POST']))
    def run():
        data = fetch_data()
        city = get_city()
        return render_template(
            'index.html', title='Home', data=data, city=city,
            form=SelectCityForm())

    # Create route to allow user to refreshd data in the database
    @app.route('/refresh', methods=(['GET', 'POST']))
    def refresh():
        """Pull fresh data from Open AQ and replace existing data."""
        if request.method == 'POST':
            city = set_city(request.form['city'])
        else:
            return redirect(url_for('run'))
        DB.drop_all()
        DB.create_all()
        params={'city': city, 'parameter': 'pm25'}  # Can configure from selection
        push_data_to_db(
            params=params,
            data=get_openaq_data(
                city=params['city'],
                parameter=params['parameter']
            ),
        )
        DB.session.commit()
        return redirect(url_for('run'))
    ## CAREFUL DO NOT DELETE THIS
    return app
    ## CAREFUL DO NOT DELETE THIS RETURN STATEMENT


# Create local instances to share across functions
def get_api():
    if 'api' not in g:
        g.api = openaq.OpenAQ()

    return g.api


# Helper functions
def get_openaq_data(city, parameter):
    api = get_api()
    results = Results(city=city, parameter=parameter)
    status, results.data = api.measurements(city=city, parameter=parameter)
    if status == 200:
        return results.get_data(('date.utc', 'value'))


def push_data_to_db(params, data):
    # hard coded to only date date_time and val right now
    print('adding data to db')
    for record in data:
        db_record = Record(datetime=record[0], value=record[1])
        DB.session.add(db_record)


def fetch_data():
    return Record.query.filter(Record.value >= 10)


def set_city(city):
    if 'city' not in g:
        g.city = city
        city = g.city

    return city

def get_city():
    if 'city' not in g:
        city = 'City not Found'
    else:
        city = g.city

    return city



# Data class
class Results():
    def __init__(self, city, parameter, data=None):
        self.city = city
        self.parameter = parameter
        self.data = data

    def get_data(self, tuple_of_columns=None):
        assert type(tuple_of_columns) == tuple
        dataframe = []
        for record in self.data['results']:
            clean_record = []
            for column in tuple_of_columns:
                if 'date' in column:
                    clean_record.append(self.strip_date(record['date'], 'utc'))
                else:
                    clean_record.append(record[column])

            dataframe.append(tuple(clean_record))

        return dataframe

    def strip_date(self, date_data, date_type):
        return date_data[date_type]

