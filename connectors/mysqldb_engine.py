# database.py

import mysql.connector
from mysql.connector import Error

class MySQLDatabase:
    def __init__(self):
        self.config = {
            "host": "grc360.cmhggsagqy8d.us-east-1.rds.amazonaws.com",
            "user": "admin",
            "password": "GoodLuck25",
            "database": "DB_GRC360"
        }

    def get_connection(self):
        return mysql.connector.connect(**self.config)

    def execute_query(self, query, params=None, fetch=False):
        """
        Executes any SQL query:
        - INSERT / UPDATE / DELETE / CREATE → fetch=False
        - SELECT → fetch=True
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(query, params)

            # If it is SELECT query
            if fetch:
                result = cursor.fetchall()
                return result

            # For CREATE, INSERT, UPDATE, DELETE
            conn.commit()
            return cursor.rowcount

        except Error as e:
            raise Exception(f"Database Error: {e}")

        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
