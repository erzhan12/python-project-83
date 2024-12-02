import os
from flask import Flask, render_template, request, url_for, redirect
from flask import flash, get_flashed_messages
from dotenv import load_dotenv
from page_analyzer.db import insert_url, read_all, read_url_by_id
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
    if messages['class'] == 'alert-danger':
        flash(messages['text'], messages['class'])
        return render_template(
            'index.html',
            messages=[(messages['class'], messages['text'])]
        ), 422

    if messages['class'] != 'alert-info':
        # insert a new row into db
        id = insert_url(url)
        if id is not None:
            messages['class'] = 'alert-success'
            messages['text'] = 'Страница успешно добавлена'
            messages['id'] = id

    flash(messages['text'], messages['class'])

    return redirect(url_for('urls_id', id=messages['id']))


@app.get('/urls')
def urls_get():
    urls = read_all()
    # logging.info(urls)
    return render_template(
        'urls.html',
        urls=urls
    ), 422


@app.get('/urls/<id>')
def urls_id(id):
    row = read_url_by_id(id)
    # logging.info(row)
    messages = get_flashed_messages(with_categories=True)
    return render_template(
            'url_show.html',
            messages=messages,
            row=row
        ), 422


# This allows the app to be run directly
if __name__ == '__main__':
    app.run(debug=True)
