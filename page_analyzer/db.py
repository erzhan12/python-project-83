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

    def __init__(self, database_url=None):
        self.database_url = database_url or os.getenv('DATABASE_URL')

        self.keepalive_kwargs = {
            "keepalives": 1,
            "keepalives_idle": 300,
            "keepalives_interval": 30,
            "keepalives_count": 5
        }

        self.connection = None

    def __enter__(self):
        """Open a new connection when used with 'with' statement."""
        self._connect_with_retries()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Ensure the connection is closed when exiting 'with' block."""
        self.close()

    def _connect_with_retries(self, retries=10, delay=3):
        """Tries to connect to the database with retries."""
        for attempt in range(1, retries + 1):
            try:
                self.connection = psycopg2.connect(
                    self.database_url,
                    **self.keepalive_kwargs
                )
                logging.info(f"✅ Database connection successful "
                             f"(attempt {attempt})")
                return
            except (Exception, psycopg2.OperationalError) as error:
                logging.warning(f"🔁 Database connection failed "
                                f"(attempt {attempt}/{retries}): {error}")
                if attempt < retries:
                    time.sleep(delay)
                else:
                    logging.error("❌ Failed to connect to the database "
                                  "after multiple attempts")
                    raise

    def get_cursor(self):
        """Creates and returns a cursor with RealDictCursor factory."""
        return self.connection.cursor(cursor_factory=RealDictCursor)

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

    def insert_check(self, url_id, url_check_result):
        """Inserts a new URL check record and returns its ID."""
        sql = ("INSERT INTO url_checks "
               "(url_id, status_code, h1, title, description) "
               "VALUES (%s, %s, %s, %s, %s) RETURNING id;")
        check_id = None

        try:
            # with self.db_connection.get_cursor() as cur:
            with self.db_connection as db:
                cur = db.get_cursor()
                cur.execute(sql, (url_id, *url_check_result))
                check_id = cur.fetchone()['id']
                self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"❌ Error inserting URL check: {error}")
            self.db_connection.rollback()

        return check_id

    def read_url_checks(self, url_id):
        """Reads all checks for a specific URL."""
        sql = ("SELECT * FROM url_checks "
               "WHERE url_id = %s ORDER BY created_at DESC;")
        rows = []

        try:
            # with self.db_connection.get_cursor() as cur:
            with self.db_connection as db:
                cur = db.get_cursor()
                cur.execute(sql, (url_id,))
                rows = cur.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"❌ Error reading URL checks: {error}")

        return rows
