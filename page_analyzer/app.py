import os

import requests
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from page_analyzer import db, html, urls

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')


# По умолчанию делаем без контроллеров, но если хотят, то пусть используют
# Все маршруты должны быть именованными
# Именование маршрутов должно соответствовать ресурсному роутингу
@app.route('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def urls_show():
    conn = db.get_db(app)
    data = db.get_urls_with_checks(conn)
    db.commit(conn)
    db.close(conn)

    return render_template(
        'urls/index.html',
        data=data,
    )


@app.post('/urls')
def post_url():
    url = request.form['url']
    # NOTE: чтобы вывести только 1 флеш сообщение с первой попавшейся ошибкой
    # Можно выводить и несколько сообщений, но лучше внутри одного алерта
    error = urls.validate(url)
    if error:
        flash(error, 'danger')
        return render_template('index.html', url_name=url), 422

    conn = db.get_db(app)
    normalized_url = urls.normalize(url)
    existed_url = db.get_url_by_name(conn, normalized_url)
    db.commit(conn)

    if existed_url:
        id = existed_url.id
        flash('Страница уже существует', 'info')
    else:
        id = db.insert_url(conn, normalized_url)
        db.commit(conn)
        flash('Страница успешно добавлена', 'success')
    db.close(conn)

    return redirect(url_for('url_show', id=id))


@app.route('/urls/<int:id>')
def url_show(id):
    conn = db.get_db(app)
    url = db.get_url_by_id(conn, id)
    db.commit(conn)
    if url is None:
        abort(404)

    checks = db.get_url_checks(conn, id)
    db.commit(conn)

    db.close(conn)

    return render_template(
        'urls/url.html',
        url=url,
        checks=checks,
    )


@app.route('/urls/<int:id>/checks', methods=['POST'])
def url_checks(id):
    conn = db.get_db(app)
    url = db.get_url_by_id(conn, id)
    db.commit(conn)

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f'Ошибка проверки {url}: {e}')
        flash('Произошла ошибка при проверке', 'alert-danger')
        return redirect(url_for('urls_id', url_id=url_id))

    page_data = html.get_page_data(resp)
    db.insert_page_check(conn, id, page_data)
    db.commit(conn)
    flash('Страница успешно проверена', 'success')
    db.close(conn)

    return redirect(url_for('url_show', id=id))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500
