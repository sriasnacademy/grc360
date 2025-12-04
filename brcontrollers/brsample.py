
from connectors.mysqldb_engine import MySQLDatabase
from connectors.pgvectordb_client import PGVectorDB

def handle_submit(entry, label):
    db = MySQLDatabase()
    name = entry.get().strip()
    
    query = """
INSERT INTO sampletable (name, department, salary)
VALUES (%s, %s, %s)
"""
    params = (name,"Computers",45000)
    if not name:
        label.config(text="Please enter name")
        return

    result = db.execute_query(query,params)
    label.config(text=result)
    

dbpg = PGVectorDB()

def create_items_table():
    
    query = """
    CREATE TABLE IF NOT EXISTS items (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        embedding vector(3)
    );
    """
    dbpg.execute(query)
    
    return insert_items()


def insert_items():
    data = [
        ("item_a", [0.1, 0.2, 0.3]),
        ("item_b", [0.4, 0.5, 0.6]),
        ("item_c", [0.7, 0.8, 0.9])
    ]

    query = "INSERT INTO items (name, embedding) VALUES (%s, %s);"

    for row in data:
        dbpg.execute(query, row)

    return "Insert completed"


def fetch_all_items():
    query = "SELECT * FROM items;"
    return dbpg.execute(query, fetch=True)
