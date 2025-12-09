from connectors.mysqldb_engine import MySQLDatabase

class GetProcess:

    def __init__(self):
        self.db = MySQLDatabase()

    def fetch_all_processes(self):
        """
        Return rows as tuples (not dictionary)
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()  # <-- NOT dictionary=True

            sql = """
                SELECT process_id, process_name, description, department,
                       process_owner, frequency, triggers, outcomes
                FROM processes
            """
            cursor.execute(sql)
            rows = cursor.fetchall()   # returns list of tuples

            return rows

        except Exception as e:
            print("Error:", e)
            return []

        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass
