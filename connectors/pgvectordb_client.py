import psycopg2
from pgvector.psycopg2 import register_vector
import os

# Database connection details (replace with your actual details)
DB_HOST = "grc-ai.cmhggsagqy8d.us-east-1.rds.amazonaws.com"
DB_NAME = "postgres"
DB_USER = "grcadmin"
DB_PASSWORD = "NewStart*25"

def create_and_insert_pgvector_data():
    conn = None
    cur = None
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()

        # Register the vector type with psycopg2
        register_vector(conn)

        # Create a table with an embedding column
        # Specify the dimension of the vector (e.g., 3 for a 3-dimensional vector)
        create_table_command = """
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            embedding vector(3) 
        );
        """
        cur.execute(create_table_command)
        conn.commit()
        print("Table 'items' created or already exists.")

        # Insert rows with vector embeddings
        data_to_insert = [
            ("item_a", [0.1, 0.2, 0.3]),
            ("item_b", [0.4, 0.5, 0.6]),
            ("item_c", [0.7, 0.8, 0.9])
        ]

        insert_command = "INSERT INTO items (name, embedding) VALUES (%s, %s);"
        for name, embedding in data_to_insert:
            cur.execute(insert_command, (name, embedding))
        conn.commit()
        print("Rows inserted successfully.")

        # Optional: Verify data
        cur.execute("SELECT * FROM items;")
        rows = cur.fetchall()
        print("\nData in 'items' table:")
        for row in rows:
            print(row)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    create_and_insert_pgvector_data()