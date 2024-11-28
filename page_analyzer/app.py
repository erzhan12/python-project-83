import os
from flask import Flask, render_template
from dotenv import load_dotenv

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


# This allows the app to be run directly
if __name__ == '__main__':
    app.run(debug=True)
