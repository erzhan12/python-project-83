from datetime import datetime

import psycopg2
from psycopg2.extras import NamedTupleCursor


def get_db(app):
    return psycopg2.connect(app.config["DATABASE_URL"])


def close(conn):
    conn.close()


def commit(conn):
    conn.commit()


def get_urls(conn):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute(
            "SELECT * FROM urls ORDER BY id DESC;",
        )
        urls = curs.fetchall()  # noqa: WPS442
    return urls


def get_checks(conn):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute(
            "SELECT DISTINCT ON (url_id) * FROM url_checks ORDER BY url_id DESC, id DESC;",  # noqa: E501
        )
        checks = curs.fetchall()
    return checks


def get_urls_with_checks(conn):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        # Делать подобный запрос через join – неправильно и сложно
        curs.execute(
            "SELECT * FROM urls ORDER BY id DESC;",
        )
        urls = curs.fetchall()  # noqa: WPS442
        curs.execute(
            "SELECT DISTINCT ON (url_id) * FROM url_checks ORDER BY url_id DESC, created_at ASC;",  # noqa: E501
        )
        checks = curs.fetchall()

    result = []
    checks_by_url_id = {check.url_id: check for check in checks}
    for url in urls:
        url_data = {}
        check = checks_by_url_id.get(url.id)
        url_data["id"] = url.id
        url_data["name"] = url.name
        url_data["last_check_date"] = check.created_at if check else ""
        url_data["status_code"] = check.status_code if check else ""
        result.append(url_data)

    return result


def get_url_by_name(conn, url):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute(
            "SELECT id, name\
            FROM urls\
            WHERE name=%s",
            (url,),
        )
        url = curs.fetchone()
    return url


def insert_url(conn, url):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute(
            "INSERT INTO urls (name, created_at)\
            VALUES (%s, %s)\
            RETURNING id;",
            (url, datetime.now()),
        )
        id = curs.fetchone().id
    return id


def get_url_by_id(conn, id):
    # Правильная выборка по первичному ключу
    with conn.cursor(cursor_factory=NamedTupleCursor) as url_curs:
        url_curs.execute(
            "SELECT * FROM urls WHERE id = %s",
            (id,),
        )
        url = url_curs.fetchone()
    return url


def get_url_checks(conn, id):
    with conn.cursor(cursor_factory=NamedTupleCursor) as check_curs:
        check_curs.execute(
            "SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;",
            (id,),
        )
        checks = check_curs.fetchall()
    return checks


def insert_page_check(conn, id, page_data):
    with conn.cursor(cursor_factory=NamedTupleCursor) as check_curs:
        check_curs.execute(
            """INSERT INTO url_checks (url_id, status_code, h1, title, description, created_at)
            VALUES (%s, %s, %s, %s, %s, %s);""",  # noqa: E501
            (
                id,
                page_data["status_code"],
                page_data["h1"],
                page_data["title"],
                page_data["description"],
                datetime.now(),
            ),  # noqa: E501
        )
