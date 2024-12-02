import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)


def insert_url(url):
    sql = "INSERT INTO urls (name) VALUES (%s) RETURNING id;"
    url_id = None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (url,))
            url_id = cur.fetchone()['id']
            conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        conn.rollback()
    finally:
        if cur:
            cur.close()
        return url_id


def read_url(url):
    sql = "SELECT * FROM urls WHERE name = %s;"
    row = None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (url,))
            row = cur.fetchone()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error reading all URLs: {error}")

    return row


def read_url_by_id(id):
    sql = "SELECT * FROM urls WHERE id = %s;"
    row = None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (id,))
            row = cur.fetchone()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error reading all URLs: {error}")
    return row


def read_url_all():
    sql = "SELECT * FROM urls ORDER BY created_at DESC;"
    rows = None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error reading all URLs: {error}")

    return rows


def insert_check(url_id):
    sql = "INSERT INTO url_checks (url_id) VALUES (%s) RETURNING id;"
    check_id = None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (url_id,))
            check_id = cur.fetchone()['id']
            conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        conn.rollback()
    finally:
        if cur:
            cur.close()
        return check_id


def read_url_checks_all(url_id):
    sql = "SELECT * FROM url_checks WHERE url_id = (%s) \
           ORDER BY created_at DESC;"
    rows = []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (url_id,))
            rows = cur.fetchall()
    except psycopg2.OperationalError as op_error:
        logging.info(f"Operational error: {op_error}")
    except psycopg2.DatabaseError as db_error:
        logging.info(f"Database error: {db_error}")
    except Exception as error:
        logging.info(f"Unexpected error: {error}")
    return rows
