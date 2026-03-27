import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_NAME = os.getenv("DB_NAME", "GH")
DB_PSSWD = os.getenv("DB_PSSWD")

conexion = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PSSWD,
    database=DB_NAME,
)

cursor = conexion.cursor()

#General CRUD

def get_all_tables(cursor):
    cursor.execute("SHOW TABLES")
    return cursor.fetchall()


def get_all_from_table(cursor, table_name):
    query = f"SELECT * FROM `{table_name}`"
    cursor.execute(query)
    return cursor.fetchall()

