import pymysql
import json
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---------------- DB CONFIG ----------------
DB_CONFIG = {
    "host": "srv840.hstgr.io",
    "user": "u567123576_grcdevuser",
    "password": "DevStart@26",
    "database": "u567123576_grc360",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "port": 3306,
    "autocommit": True,
    "connect_timeout": 10
}


# ---------------- DB CONNECTION ----------------
def get_connection():
    return pymysql.connect(**DB_CONFIG)


# ---------------- RESPONSE FORMAT ----------------
def response(status, body):
    return {
        "statusCode": status,
        "body": json.dumps(body, default=str)
    }


# ---------------- MAIN HANDLER ----------------
def lambda_handler(event, context):
    try:
        logger.info(f"EVENT: {event}")

        raw_body = event.get("body", event)
        body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body

        action = body.get("action")
        table = body.get("table")

        if not action:
            return response(400, {"error": "Missing 'action'"})

        if action != "raw_sql" and not table:
            return response(400, {"error": "Missing 'table'"})

        if action == "insert":
            return insert_data(table, body.get("data"))

        elif action == "update":
            return update_data(table, body.get("data"), body.get("where"))

        elif action == "select":
            return select_data(table, body.get("columns"), body.get("where"))

        elif action == "delete":
            return delete_data(table, body.get("where"))

        elif action == "raw_sql":
            return raw_sql(body.get("sql"), body.get("params"))

        else:
            return response(400, {"error": "Invalid action type"})

    except Exception as e:
        return response(500, {"error": str(e), "type": type(e).__name__})



# ---------------- INSERT ----------------
def insert_data(table, data):
    if not data:
        return response(400, {"error": "Missing 'data' for insert"})

    cols = ", ".join(data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    values = list(data.values())

    query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"

    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(query, values)
        inserted_id = cursor.lastrowid
    conn.close()

    return response(200, {
        "message": "Insert successful",
        "inserted_id": inserted_id
    })


# ---------------- UPDATE ----------------
def update_data(table, data, where):
    if not data or not where:
        return response(400, {"error": "Both 'data' and 'where' required for update"})

    set_clause = ", ".join([f"{k}=%s" for k in data])
    where_clause = " AND ".join([f"{k}=%s" for k in where])

    values = list(data.values()) + list(where.values())

    query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

    conn = get_connection()
    with conn.cursor() as cursor:
        rows = cursor.execute(query, values)
    conn.close()

    return response(200, {
        "message": "Update successful",
        "rows_affected": rows
    })


# ---------------- SELECT ----------------
def select_data(table, columns=None, where=None):
    cols = ", ".join(columns) if columns else "*"
    query = f"SELECT {cols} FROM {table}"
    values = []

    if where:
        clauses = []

        for key, value in where.items():
            # ✅ SUPPORT LIST → IN clause
            if isinstance(value, list):
                placeholders = ", ".join(["%s"] * len(value))
                clauses.append(f"{key} IN ({placeholders})")
                values.extend(value)
            else:
                clauses.append(f"{key} = %s")
                values.append(value)

        where_clause = " AND ".join(clauses)
        query += f" WHERE {where_clause}"

    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(query, values)
        records = cursor.fetchall()
    conn.close()

    return response(200, {
        "count": len(records),
        "records": records
    })



# ---------------- DELETE ----------------
def delete_data(table, where):
    if not where:
        return response(400, {"error": "Missing 'where' for delete"})

    where_clause = " AND ".join([f"{k}=%s" for k in where])
    values = list(where.values())

    query = f"DELETE FROM {table} WHERE {where_clause}"

    conn = get_connection()
    with conn.cursor() as cursor:
        rows = cursor.execute(query, values)
    conn.close()

    return response(200, {
        "message": "Delete successful",
        "rows_deleted": rows
    })

def raw_sql(sql, params=None):
    if not sql:
        return response(400, {"error": "Missing 'sql' for raw_sql action"})

    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(sql, params or [])
        records = cursor.fetchall()
        inserted_id = cursor.lastrowid
    conn.close()

    return response(200, {
        "count": len(records),
        "records": records,
        "inserted_id": inserted_id
    })
