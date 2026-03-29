from DB.connector import DatabaseConnector
import json
class Repo:
    def __init__(self, **data):
        for key, value in data.items():
            setattr(self, key, str(value))

    def __repr__(self):
        return (self.name)

    def __str__(self):
        return (self.name)

    def create_table(self):
        db = DatabaseConnector()
        cursor = db.cursor

        columns = []
        for key in self.__dict__.keys():
            if key == "id":
                columns.append(f"{key} VARCHAR(255) PRIMARY KEY")
            else:
                columns.append(f"{key} TEXT")

        columns_sql = ",\n            ".join(columns)

        query = f"""
        CREATE TABLE IF NOT EXISTS repos (
            {columns_sql}
        )
        """

        cursor.execute(query)
        db.connection.commit()
        db.close()


    def repo_in_db(self):
        db = DatabaseConnector()
        repo_names = db.get_repos()
        return self.name in repo_names

    def save(self):

        db = DatabaseConnector()
        cursor = db.cursor

        # obtener atributos del objeto
        data = self.__dict__

        self.create_table()

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        values = tuple(
            json.dumps(i) if isinstance(i, (dict, list)) else str(i)
            for i in data.values()
        )

        query = f"INSERT INTO repos ({columns}) VALUES ({placeholders})"

        cursor.execute(query, values)
        db.connection.commit()
        print(f'repo {self.id} saved in db')
        db.close()



