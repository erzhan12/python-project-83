import os
import time
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class DatabaseConnection:
    """Manages database connection and provides connection utilities."""

    def __init__(self, database_url):
        self.database_url = database_url
        self.connection = None

        self.keepalive_kwargs = {
            "keepalives": 1,
            "keepalives_idle": 300,
            "keepalives_interval": 30,
            "keepalives_count": 5
        }

        self.connection = None
        self._connect_with_retries()

    def __enter__(self):
        """Open a new connection when used with 'with' statement."""
        self._connect_with_retries()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Ensure the connection is closed when exiting 'with' block."""
        self.close()



    def connect_with_retries(self, retries=10, delay=3):
        """Tries to connect to the database with retries."""
        for attempt in range(1, retries + 1):
            try:
                self.connection = psycopg2.connect(self.database_url)
                self.connection.autocommit = True
                print(f"✅ Database connected (attempt {attempt})")
                return
            except psycopg2.OperationalError as error:
                if "database system is starting up" in str(error):
                    print(f"⏳ Database is starting up, retrying in {delay} sec...")
                    time.sleep(delay)
                else:
                    print(f"❌ Database connection failed: {error}")
                    if attempt == retries:
                        raise

    def get_cursor(self):
        """Returns a new cursor and ensures the connection is open."""
        if self.connection is None or self.connection.closed:
            print("🔄 Reconnecting to the database...")
            self.connect_with_retries()
        return self.connection.cursor()

    def commit(self):
        """Commits the current transaction."""
        self.connection.commit()

    def rollback(self):
        """Rolls back the current transaction."""
        self.connection.rollback()

    def close(self):
        """Closes the database connection."""
        if self.connection:
            self.connection.close()


class URLManager:
    """Manages operations related to URLs in the database."""

    def __init__(self, db_connection):
        self.db_connection = db_connection

    def insert_url(self, url):
        """Inserts a new URL into the database and returns its ID."""
        sql = "INSERT INTO urls (name) VALUES (%s) RETURNING id;"
        url_id = None

        try:
            # with self.db_connection.get_cursor() as cur:
            with self.db_connection as db:
                cur = db.get_cursor()
                cur.execute(sql, (url,))
                url_id = cur.fetchone()['id']
                self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"❌ Error inserting URL: {error}")
            self.db_connection.rollback()

        return url_id

    def read_url(self, url=None, url_id=None):
        """Reads a URL record by name or ID."""
        if url:
            sql = "SELECT * FROM urls WHERE name = %s;"
            param = (url,)
        elif url_id:
            sql = "SELECT * FROM urls WHERE id = %s;"
            param = (url_id,)
        else:
            raise ValueError("Either url or url_id must be provided")

        row = None
        try:
            # with self.db_connection.get_cursor() as cur:
            with self.db_connection as db:
                cur = db.get_cursor()
                cur.execute(sql, param)
                row = cur.fetchone()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"❌ Error reading URL: {error}")

        return row

    def read_all_urls(self):
        """Reads all URLs from the database."""
        sql = "SELECT * FROM urls ORDER BY created_at DESC;"
        rows = []

        try:
            # with self.db_connection.get_cursor() as cur:
            with self.db_connection as db:
                cur = db.get_cursor()
                cur.execute(sql)
                rows = cur.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"❌ Error reading all URLs: {error}")

        return rows

    def read_url_with_latest_checks(self):
        """Reads URLs along with their latest check results."""
        sql = """
        SELECT
            urls.id,
            urls.name,
            COALESCE(TO_CHAR(latest_check.created_at, 'YYYY-MM-DD'),
            '') AS latest_created_at,
            COALESCE(latest_check.status_code::text, '') AS latest_status_code
        FROM urls
        LEFT OUTER JOIN (
            SELECT DISTINCT ON (url_id) url_id, created_at, status_code
            FROM url_checks
            ORDER BY url_id, created_at DESC
        ) AS latest_check ON urls.id = latest_check.url_id
        ORDER BY urls.id DESC;
        """
        rows = []

        try:
            # with self.db_connection.get_cursor() as cur:
            with self.db_connection as db:
                cur = db.get_cursor()
                cur.execute(sql)
                rows = cur.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"❌ Error reading URLs with latest checks: {error}")

        return rows


class URLCheckManager:
    """Manages operations related to URL checks in the database."""

    def __init__(self, db_connection):
        self.db_connection = db_connection

    def read_url_checks(self, url_id):
        """Fetches all checks for a given URL."""
        sql = "SELECT * FROM url_checks WHERE url_id = %s ORDER BY created_at DESC;"
        checks = []
        try:
            with self.db_connection.get_cursor() as cur:
                cur.execute(sql, (url_id,))
                checks = cur.fetchall()
                print(f"🔍 Retrieved checks for URL ID {url_id}: {checks}")
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"❌ Error reading URL checks: {error}")
        return checks

    def insert_check(self, url_id, url_check_result):
        """Inserts a new URL check record and returns its ID."""
        sql = ("INSERT INTO url_checks (url_id, status_code, h1, title, description) "
               "VALUES (%s, %s, %s, %s, %s) RETURNING id;")
        check_id = None

        try:
            with self.db_connection.get_cursor() as cur:
                logging.info(f"📥 Inserting check into DB: {url_check_result}")  # Логируем перед вставкой
                cur.execute(sql, (url_id, *url_check_result))
                check_id = cur.fetchone()['id']
                logging.info(f"✅ Inserted check ID: {check_id}")
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"❌ Error inserting URL check: {error}")
            self.db_connection.rollback()

        return check_id

    def read_url(self, url=None, url_id=None):
        """Reads a URL record by name or ID."""
        if url:
            sql = "SELECT * FROM urls WHERE name = %s;"
            param = (url,)
        elif url_id:
            sql = "SELECT * FROM urls WHERE id = %s;"
            param = (url_id,)
        else:
            raise ValueError("Either url or url_id must be provided")

        row = None
        try:
            with self.db_connection.get_cursor() as cur:
                cur.execute(sql, param)
                row = cur.fetchone()
                logging.info(f"🔎 Found URL in DB: {row}")  # Логируем результат
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"❌ Error reading URL: {error}")

        return row

