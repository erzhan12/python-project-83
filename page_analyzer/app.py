import os
from flask import Flask, render_template, request, url_for, redirect
from flask import flash, get_flashed_messages
from dotenv import load_dotenv
from page_analyzer.db import insert_url, read_url_all, read_url_by_id
from page_analyzer.db import insert_check, read_url_checks_all
from page_analyzer.validator import validate
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Create Flask application
app = Flask(__name__)

# Set secret key from environment variable
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


# First route handler
@app.route('/')
def index():
    return render_template('index.html')


@app.post('/urls')
def urls_post():
    url = request.form.get('url')
    # logging.info(url)

    messages = validate(url)
    if messages and messages['class'] == 'alert-danger':
        # flash(messages['text'], messages['class'])
        return render_template(
            'index.html',
            messages=[(messages['class'], messages['text'])]
        ), 422

    if not messages or messages['class'] != 'alert-info':
        # insert a new row into db
        id = insert_url(url)
        if id is not None:
            messages['class'] = 'alert-success'
            messages['text'] = 'Страница успешно добавлена'
            messages['id'] = id

    flash(messages['text'], messages['class'])

    return redirect(url_for('urls_id', id=messages['id']))


@app.route('/urls')
def urls_get():
    urls = read_url_all()
    # logging.info(urls)
    return render_template(
        'urls.html',
        urls=urls
    ), 422


@app.get('/urls/<id>')
def urls_id(id):
    url_row = read_url_by_id(id)
    url_checks = read_url_checks_all(id)
    logging.info(url_row)
    messages = get_flashed_messages(with_categories=True)
    return render_template(
            'url_show.html',
            messages=messages,
            url_row=url_row,
            url_checks=url_checks
        ), 422


@app.post('/urls/<id>/checks')
def urls_checks_post(id):
    # read url by id
    url_row = read_url_by_id(id)
    # perform checking
    # TODO
    # insert new check into DB table
    insert_check(id)
    # read all checks from db table
    url_checks = read_url_checks_all(id)
    # return render url_show checks=checks
    return render_template(
        'url_show.html',
        url_checks=url_checks,
        url_row=url_row
    ), 422


# This allows the app to be run directly
if __name__ == '__main__':
    app.run(debug=True)
