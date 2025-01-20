import os
import requests
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from page_analyzer.utilities import (
    parse_url,
    parse_response,
    validate_url
)
from page_analyzer.url_repository import UrlRepository


app = Flask(__name__)
load_dotenv()
database_url = os.getenv('DATABASE_URL')
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/not_found.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/server_error.html'), 500


@app.route('/')
def home_page():
    errors = {}
    url_adress = request.args.get('url', '')
    return render_template(
        'index.html',
        search=url_adress,
        errors=errors
    )


@app.post('/urls')
def post_url():
    entered_address = request.form.to_dict()
    normalized_url = parse_url(entered_address['url'])
    errors = validate_url(normalized_url)

    if errors:
        flash('Некорректный URL', 'danger')
        return render_template(
            'index.html',
            search=normalized_url,
            errors=errors
        ), 422

    repo = UrlRepository(database_url)
    url_info = repo.find_url(normalized_url)
    if url_info is not None:
        flash('Страница уже существует', 'warning')
        return redirect(url_for('get_url', id=url_info.get('id')), code=302)

    id = repo.add_url(normalized_url)
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('get_url', id=id), code=302)


@app.route('/urls/<int:id>')
def get_url(id):
    repo = UrlRepository(database_url)
    url_info = repo.find_id(id)

    if not url_info:
        abort(404)

    url_check = repo.get_checks(id)
    return render_template(
        'urls/url_checks.html',
        url_info=url_info,
        url_check=url_check
    )


@app.route('/urls')
def get_urls_list():
    repo = UrlRepository(database_url)
    urls = repo.get_content()

    return render_template(
        'urls/urls_list.html',
        urls=urls
    )


@app.post('/urls/<int:id>/cheks')
def post_url_check(id):
    repo = UrlRepository(database_url)
    url_info = repo.find_id(id)

    try:
        response = requests.get(url_info.get('name'), timeout=0.3)
        response.raise_for_status()
    except requests.RequestException:
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('get_url', id=id))

    status = response.status_code
    analysis = parse_response(response)

    check_info = repo.check(
        url_info,
        status,
        analysis
    )

    flash('Страница успешно проверена', 'success')
    return redirect(url_for('get_url', id=check_info.get('url_id')), code=302)