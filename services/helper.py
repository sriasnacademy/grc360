import re

def build_lambda_payload_from_query(sql: str) -> dict:
    if not sql or not sql.strip():
        raise ValueError("Empty SQL")

    sql = sql.strip().rstrip(";")

    # SELECT columns
    select_match = re.search(r"select\s+(.*?)\s+from\s", sql, re.IGNORECASE)
    if not select_match:
        raise ValueError("Invalid SELECT clause")

    columns = [c.strip() for c in select_match.group(1).split(",")]

    # FROM table
    from_match = re.search(r"from\s+(\w+)", sql, re.IGNORECASE)
    if not from_match:
        raise ValueError("Invalid FROM clause")

    table = from_match.group(1)

    # WHERE clause
    where = {}
    where_match = re.search(r"where\s+(.*?)($|\s+order\s+by)", sql, re.IGNORECASE)
    if where_match:
        conditions = where_match.group(1).split("and")
        for cond in conditions:
            if "=" not in cond:
                continue
            key, val = cond.split("=", 1)
            val = val.strip().strip("'")

            if val.isdigit():
                val = int(val)

            where[key.strip()] = val

    # ORDER BY
    order_by = None
    order_match = re.search(r"order\s+by\s+(\w+)", sql, re.IGNORECASE)
    if order_match:
        order_by = order_match.group(1)

    payload = {
        "action": "select",
        "table": table,
        "columns": columns
    }

    if where:
        payload["where"] = where

    if order_by:
        payload["order_by"] = order_by

    return payload
