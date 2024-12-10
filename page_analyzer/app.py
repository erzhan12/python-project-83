import os
from flask import Flask, render_template, request, url_for, redirect
from flask import flash, get_flashed_messages
from dotenv import load_dotenv
from page_analyzer.validator import URLValidator
from page_analyzer.url_checker import URLChecker
import logging
from page_analyzer.db import URLManager, URLCheckManager, DatabaseConnection
from urllib.error import HTTPError
from requests.exceptions import RequestException

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Create Flask application
app = Flask(__name__)

# Set secret key from environment variable
app.config['SECRET_KEY'] = "3bb41977871bb5de0339a57e3cc1d720"
# os.getenv('SECRET_KEY')

# Create a database connection
db_connection = DatabaseConnection(os.getenv('DATABASE_URL'))

# Create managers
url_manager = URLManager(db_connection)
url_check_manager = URLCheckManager(db_connection)

# Create URL Validator
url_validator = URLValidator(url_manager)

# Create URL Checker
url_checker = URLChecker()


# First route handler
@app.route('/')
def index():
    return render_template('index.html')


@app.post('/urls')
def urls_post():
    url = request.form.get('url')
    # logging.info(url)

    messages = url_validator.validate(url)
    logging.info(f'Validation result: {messages}')
    if messages and messages['class'] == 'alert-danger':
        return render_template(
            'index.html',
            messages=[(messages['class'], messages['text'])]
        ), 422

    if not messages or messages['class'] != 'alert-info':
        # insert a new row into db
        url_id = url_manager.insert_url(url)
        if url_id is not None:
            messages['class'] = 'alert-success'
            messages['text'] = 'Страница успешно добавлена'
            messages['id'] = url_id

    flash(messages['text'], messages['class'])

    return redirect(url_for('urls_id', url_id=messages['id']))


@app.route('/urls')
def urls_get():
    # urls = url_manager.read_all_urls()
    urls_with_latest_checks = url_manager.read_url_with_latest_checks()
    # logging.info(urls)
    return render_template(
        'urls.html',
        urls=urls_with_latest_checks
    ), 422


@app.get('/urls/<url_id>')
def urls_id(url_id):
    logging.info(f'Start reading url by id: {url_id}')
    # url_row = read_url_by_id(id)
    url_row = url_manager.read_url(url_id=url_id)
    logging.info(f'End reading url by id: {url_id} result: {url_row['name']}')
    # url_checks = read_url_checks_all(id)
    url_checks = url_check_manager.read_url_checks(url_id=url_id)
    # logging.info(url_checks)
    messages = get_flashed_messages(with_categories=True)
    return render_template(
            'url_show.html',
            messages=messages,
            url_row=url_row,
            url_checks=url_checks
        ), 422


@app.post('/urls/<url_id>/checks')
def urls_checks_post(url_id):
    url_check_result = None
    # read url by id
    url_row = url_manager.read_url(url_id=url_id)
    # perform checking
    try:
        url_check_result = url_checker.check(url_row['name'])
    except (HTTPError, RequestException):
        flash('Произошла ошибка при проверке')
    # insert new check into DB table
    if url_check_result:
        logging.info(f'URL Check Result: {url_check_result}')
        url_check_manager.insert_check(url_id, url_check_result)

    # read all checks from db table
    url_checks = url_check_manager.read_url_checks(url_id)
    # return render url_show checks=checks
    return render_template(
        'url_show.html',
        url_checks=url_checks,
        url_row=url_row
    ), 422


# This allows the app to be run directly
if __name__ == '__main__':
    app.run(debug=True)
