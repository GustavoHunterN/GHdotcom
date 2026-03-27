from control.classes import class_validator
from DB.Conector import cursor, conexion
class Repo:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)



    def __repr__(self):
        return self.__dict__['name']

    def __str__(self):
        return f"{self.__class__.__name__}: {self.__dict__['name']}"

    def create_table(self, cursor):
        columns = []

        for key, value in self.__dict__.items():
            if isinstance(value, bool):
                sql_type = "BOOLEAN"
            elif isinstance(value, int):
                sql_type = "BIGINT"
            elif isinstance(value, float):
                sql_type = "DOUBLE"
            elif isinstance(value, str):
                sql_type = "TEXT"
            elif isinstance(value, (dict, list)):
                sql_type = "JSON"  # usar TEXT si tu DB no soporta JSON
            else:
                sql_type = "TEXT"

            if key == "id":
                columns.append(f"`{key}` {sql_type} PRIMARY KEY")
            else:
                columns.append(f"`{key}` {sql_type}")

        columns_sql = ",\n    ".join(columns)

        query = f"""
        CREATE TABLE IF NOT EXISTS repo (
            {columns_sql}
        );
        """

        cursor.execute(query)


    def show_columns(self, cursor):
        cursor.execute("SHOW COLUMNS FROM repo")
        return cursor.fetchall()



    def show_(self, cursor):
        cursor.execute("SELECT * FROM repo")
        return cursor.fetchall()


    def ClassValidator(self, request):
        if class_validator(self, request):
            pass
        else:
            raise Exception(f"{self.__class__.__name__} is not valid")

    def save(self, cursor):
        import json

        keys = []
        values = []
        placeholders = []

        for key, value in self.__dict__.items():
            keys.append(f"`{key}`")

            if isinstance(value, (dict, list)):
                values.append(json.dumps(value))
            else:
                values.append(value)

            placeholders.append("%s")

        keys_sql = ", ".join(keys)
        placeholders_sql = ", ".join(placeholders)

        query = f"INSERT IGNORE INTO `repo` ({keys_sql}) VALUES ({placeholders_sql})"
        cursor.execute(query, tuple(values))
        conexion.commit()


