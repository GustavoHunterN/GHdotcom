from dotenv import load_dotenv
import requests
import os

from DB.connector import DatabaseConnector


class GitHubClient:

    def __init__(self):
        try:
            load_dotenv()
        except Exception as e:
            print(e)

        self.token = os.getenv('GITHUB_TOKEN')
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json"
        }
        self.BASE_URL = 'https://api.github.com'
        self.user = 'user'
        self.repo = 'repo'



    def get_repos(self):
        url = F'{self.BASE_URL}/{self.user}/repos'
        response = requests.get(url, headers=self.headers)
        return response.json()


    def get_repo_names(self):
        raw = self.get_repos()
        names = [str(r['name']) for r in raw]
        return names


    def get_repo_by_name(self, name):
        url = f"{self.BASE_URL}/repos/{self.user}/{name}"

        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.text}")
        return response.json()






