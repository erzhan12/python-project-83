import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


class DatabaseConnection:
    """Manages database connection and provides connection utilities."""

    def __init__(self, database_url=None):
        """
        Initialize the database connection.

        :param database_url: Database connection URL
        (optional, defaults to environment variable)
        """
        load_dotenv()
        self.database_url = database_url or os.getenv('DATABASE_URL')

        # Keepalive configuration to maintain connection stability
        self.keepalive_kwargs = {
            "keepalives": 1,
            "keepalives_idle": 60,
            "keepalives_interval": 10,
            "keepalives_count": 5
        }

        self.connection = None
        self._connect()

    def _connect(self):
        """Establish a database connection."""
        try:
            self.connection = psycopg2.connect(
                self.database_url,
                **self.keepalive_kwargs
            )
        except (Exception, psycopg2.Error) as error:
            logging.error(f"Error connecting to database: {error}")
            raise

    def get_cursor(self):
        """
        Create and return a cursor with RealDictCursor factory.

        :return: Database cursor
        """
        return self.connection.cursor(cursor_factory=RealDictCursor)

    def commit(self):
        """Commit the current transaction."""
        self.connection.commit()

    def rollback(self):
        """Rollback the current transaction."""
        self.connection.rollback()

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()


class URLManager:
    """Manages operations related to URLs in the database."""

    def __init__(self, db_connection):
        """
        Initialize URLManager with a database connection.

        :param db_connection: DatabaseConnection instance
        """
        self.db_connection = db_connection

    def insert_url(self, url):
        """
        Insert a new URL into the database.

        :param url: URL to insert
        :return: Inserted URL's ID or None
        """
        sql = "INSERT INTO urls (name) VALUES (%s) RETURNING id;"
        url_id = None

        try:
            with self.db_connection.get_cursor() as cur:
                cur.execute(sql, (url,))
                url_id = cur.fetchone()['id']
                self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Error inserting URL: {error}")
            self.db_connection.rollback()

        return url_id

    def read_url(self, url=None, url_id=None):
        """
        Read URL by name or ID.

        :param url: URL name to search (optional)
        :param url_id: URL ID to search (optional)
        :return: URL record or None
        """
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
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Error reading URL: {error}")

        return row

    def read_all_urls(self):
        """
        Read all URLs from the database.

        :return: List of URL records
        """
        sql = "SELECT * FROM urls ORDER BY created_at DESC;"
        rows = []

        try:
            with self.db_connection.get_cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Error reading all URLs: {error}")

        return rows


class URLCheckManager:
    """Manages operations related to URL checks in the database."""

    def __init__(self, db_connection):
        """
        Initialize URLCheckManager with a database connection.

        :param db_connection: DatabaseConnection instance
        """
        self.db_connection = db_connection

    def insert_check(self, url_id):
        """
        Insert a new URL check record.

        :param url_id: ID of the URL to check
        :return: Inserted check record's ID or None
        """
        sql = "INSERT INTO url_checks (url_id) VALUES (%s) RETURNING id;"
        check_id = None

        try:
            with self.db_connection.get_cursor() as cur:
                cur.execute(sql, (url_id,))
                check_id = cur.fetchone()['id']
                self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Error inserting URL check: {error}")
            self.db_connection.rollback()

        return check_id

    def read_url_checks(self, url_id):
        """
        Read all checks for a specific URL.

        :param url_id: ID of the URL
        :return: List of URL check records
        """
        sql = ("SELECT * FROM url_checks WHERE url_id = (%s) "
               "ORDER BY created_at DESC;")
        rows = []

        try:
            with self.db_connection.get_cursor() as cur:
                cur.execute(sql, (url_id,))
                rows = cur.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Error reading URL checks: {error}")
        return rows

# import psycopg2
# from psycopg2.extras import RealDictCursor
# import os
# import logging
# from dotenv import load_dotenv
# load_dotenv()
# DATABASE_URL = os.getenv('DATABASE_URL')

# keepalive_kwargs = {
#     "keepalives": 1,
#     "keepalives_idle": 60,
#     "keepalives_interval": 10,
#     "keepalives_count": 5
# }

# conn = psycopg2.connect(DATABASE_URL, **keepalive_kwargs)


# def insert_url(url):
#     sql = "INSERT INTO urls (name) VALUES (%s) RETURNING id;"
#     url_id = None
#     try:
#         with conn.cursor(cursor_factory=RealDictCursor) as cur:
#             cur.execute(sql, (url,))
#             url_id = cur.fetchone()['id']
#             conn.commit()
#     except (Exception, psycopg2.DatabaseError) as error:
#         logging.info(error)
#         conn.rollback()
#     finally:
#         return url_id


# def read_url(url):
#     sql = "SELECT * FROM urls WHERE name = %s;"
#     row = None
#     try:
#         with conn.cursor(cursor_factory=RealDictCursor) as cur:
#             cur.execute(sql, (url,))
#             row = cur.fetchone()
#     except (Exception, psycopg2.DatabaseError) as error:
#         logging.info(f"Error reading URL: {error}")

#     return row


# def read_url_by_id(id):
#     sql = "SELECT * FROM urls WHERE id = %s;"
#     row = None
#     try:
#         with conn.cursor(cursor_factory=RealDictCursor) as cur:
#             cur.execute(sql, (id,))
#             row = cur.fetchone()
#     except (Exception, psycopg2.DatabaseError) as error:
#         logging.info(f"Error reading URL by ID: {error}")
#     return row


# def read_url_all():
#     sql = "SELECT * FROM urls ORDER BY created_at DESC;"
#     rows = []
#     try:
#         with conn.cursor(cursor_factory=RealDictCursor) as cur:
#             cur.execute(sql)
#             rows = cur.fetchall()
#     except (Exception, psycopg2.DatabaseError) as error:
#         logging.info(f"Error reading all URLs: {error}")

#     return rows


# def insert_check(url_id):
#     sql = "INSERT INTO url_checks (url_id) VALUES (%s) RETURNING id;"
#     check_id = None
#     try:
#         with conn.cursor(cursor_factory=RealDictCursor) as cur:
#             cur.execute(sql, (url_id,))
#             check_id = cur.fetchone()['id']
#             conn.commit()
#     except (Exception, psycopg2.DatabaseError) as error:
#         logging.info(error)
#         conn.rollback()
#     finally:
#         return check_id


# def read_url_checks_all(url_id):
#     sql = "SELECT * FROM url_checks WHERE url_id = (%s) \
#            ORDER BY created_at DESC;"
#     rows = []
#     try:
#         with conn.cursor(cursor_factory=RealDictCursor) as cur:
#             cur.execute(sql, (url_id,))
#             rows = cur.fetchall()
#     except (Exception, psycopg2.DatabaseError) as error:
#         logging.info(f"Error reading URL Checks: {error}")
#     return rows
