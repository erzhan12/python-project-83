import os
from flask import Flask, render_template, request, url_for
from dotenv import load_dotenv
from page_analyzer.db import insert_url
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
    logging.info(url)

    errors = validate(url)
    if errors:
        return render_template(
            'index.html',
            errors=errors
        ), 422

    # insert a new row into db
    insert_url(url)

    return {'message': 'URL received', 'url': url}


# This allows the app to be run directly
if __name__ == '__main__':
    app.run(debug=True)
