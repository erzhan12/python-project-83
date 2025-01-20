import os
import time
import logging
import psutil
from flask import Flask, render_template, request, url_for
from flask import redirect, flash, get_flashed_messages
from dotenv import load_dotenv
from page_analyzer.validator import URLValidator
from page_analyzer.url_checker import URLChecker
from page_analyzer.db import URLManager, URLCheckManager, DatabaseConnection
from urllib.error import HTTPError
from requests.exceptions import RequestException
from page_analyzer.config import config

# ✅ Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,  # Можно поменять на DEBUG, если нужно больше деталей
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = config.APP_CONFIG.secret_key

db_connection = DatabaseConnection(os.getenv('DATABASE_URL'))
url_manager = URLManager(db_connection)
url_check_manager = URLCheckManager(db_connection)

url_validator = URLValidator(url_manager)
url_checker = URLChecker()


def log_resources():
    process = psutil.Process()
    logging.info(f"🔥 CPU: {process.cpu_percent()}% | RAM: "
                 f"{process.memory_info().rss / 1024 / 1024:.2f} MB")


@app.before_request
def start_timer():
    request.start_time = time.time()
    log_resources()


@app.after_request
def log_request(response):
    duration = time.time() - request.start_time
    logging.info(f"⏱️ {request.method} {request.path} | "
                 f"{response.status_code} | {duration:.3f}s")
    return response


@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"❌ Ошибка: {str(e)}")
    return "Internal Server Error", 500


@app.route('/')
def index():
    return render_template('index.html')


@app.post('/urls')
def urls_post():
    """Handles the addition of a new URL to the database."""
    url = request.form.get('url')
    messages = url_validator.validate(url)

    logging.info(f'🔎 Проверка URL: {url} | Результат: {messages}')

    if messages and messages['class'] == 'alert-danger':
        flash(messages['text'], messages['class'])
        return render_template('index.html', messages=[(messages['class'], messages['text'])]), 422

    existing_url = url_manager.read_url_by_name(url)
    if existing_url:
        messages = {'class': 'alert-info', 'text': 'Страница уже существует', 'id': existing_url["id"]}
        flash(messages['text'], messages['class'])
        return redirect(url_for('urls_id', url_id=messages['id']))

    url_id = url_manager.insert_url(url)

    if url_id is not None:
        messages = {'class': 'alert-success', 'text': 'Страница успешно добавлена', 'id': url_id}
        flash(messages['text'], messages['class'])

    return redirect(url_for('urls_id', url_id=messages['id']))


@app.route('/urls')
def urls_get():
    start_time = time.time()
    urls_with_latest_checks = url_manager.read_url_with_latest_checks()
    duration = time.time() - start_time
    logging.info(f"📄 Чтение всех URL заняло {duration:.3f}s")

    return render_template(
        'urls.html',
        urls=urls_with_latest_checks
    ), 200


@app.get('/urls/<url_id>')
def urls_id(url_id):
    logging.info(f'🔎 Получение URL по ID: {url_id}')
    start_time = time.time()
    url_row = url_manager.read_url(url_id=url_id)
    url_checks = url_check_manager.read_url_checks(url_id=url_id)
    duration = time.time() - start_time

    logging.info(f'✅ Запрос URL завершен за {duration:.3f}s |'
                 f' {url_row["name"]}')

    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'url_show.html',
        messages=messages,
        url_row=url_row,
        url_checks=url_checks
    ), 200


@app.post('/urls/<url_id>/checks')
def urls_checks_post(url_id):
    """Performs a check on the given URL."""
    url_row = url_manager.read_url(url_id=url_id)
    url_check_result = None

    try:
        url_check_result = url_checker.check(url_row['name'])
        print(f'✅ Успешная проверка: {url_check_result}')
    except (HTTPError, RequestException) as e:
        print(f"❌ Ошибка при проверке {url_row['name']}: {e}")
        flash('Произошла ошибка при проверке', 'alert-danger')

    if url_check_result:
        url_check_manager.insert_check(url_id, url_check_result)
        flash('Страница успешно проверена', 'alert-success')

    return redirect(url_for('urls_id', url_id=url_id))



if __name__ == '__main__':
    app.run(debug=True)
