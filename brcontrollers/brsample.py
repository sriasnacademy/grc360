
from connectors.mysqldb_engine import MySQLDatabase

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