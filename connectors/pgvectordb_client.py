# db_pgvector.py

import psycopg2
from pgvector.psycopg2 import register_vector

class PGVectorDB:

    def __init__(self):
        self.config = {
            "host": "grc-ai.cmhggsagqy8d.us-east-1.rds.amazonaws.com",
            "database": "postgres",
            "user": "grcadmin",
            "password": "NewStart*25"
        }

    def connect(self):
        conn = psycopg2.connect(**self.config)
        register_vector(conn)
        return conn

    def execute(self, query, params=None, fetch=False):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute(query, params)

        if fetch:
            result = cur.fetchall()
        else:
            conn.commit()
            result = cur.rowcount

        cur.close()
        conn.close()
        return result
