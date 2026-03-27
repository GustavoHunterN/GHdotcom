import os
from dotenv import load_dotenv
import requests
from modules.repo import Repo
from DB.Conector import cursor, conexion

load_dotenv()


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise Exception("GITHUB_TOKEN environment variable not set")


headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}"
}

response = requests.get("https://api.github.com/user", headers=headers)

user_id = response.json()["id"]
repos = requests.get("https://api.github.com/user/repos", headers=headers)


print(repos.json()[0].values())

for repo in repos.json():

        objeto = Repo(**repo)
        objeto.create_table(cursor)
        objeto.save(cursor)
        tables = objeto.show_table(cursor)
        print(f'tablas {tables}')










