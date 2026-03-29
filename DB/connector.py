import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnector:
    def __init__(self):
        self.connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )

        # cursor para ejecutar queries
        self.cursor = self.connection.cursor()

    def get_repos(self):
        self.cursor.execute(
            "SELECT name FROM repos;"
        )

        raw = self.cursor.fetchall()
        names = [r[0] for r in raw]

        return names


    def close(self):
        self.cursor.close()
        self.connection.close()



