import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)


def insert_url(url):
    sql = "INSERT INTO urls (name) VALUES (%s);"

    try:
        with conn.cursor as cur:
            cur.execute(sql, (url,))

            rows = cur.fetchone()
            if rows:
                url_id = rows[0]

            conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        return url_id
