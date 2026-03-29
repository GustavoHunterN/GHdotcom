from DB.connector import DatabaseConnector
from API_GitHub.GithubClient import GitHubClient
from API_GitHub.repo import Repo
"""Checks if repo exists in db"""

def repo_missing_in_db():
    client = GitHubClient()
    repos = client.get_repo_names()
    db = DatabaseConnector()
    return [ide for ide in repos if ide not in db.get_repos()]

def add_repo_to_db(repo_id):
    client = GitHubClient()
    if isinstance(repo_id, list):
        for ide in repo_id:
            repo = client.get_repo_by_name(ide)
            print('repo: ', repo)
            repoobj = Repo(**repo)
            if not repoobj.repo_in_db():
                repoobj.save()
            else:
                print("repo already exists in db")

    else:
        repo = client.get_repo_by_name(repo_id)
        repoobj = Repo(**repo)
        if not repoobj.repo_in_db():
            repoobj.save()
        else:
            print("repo already exists in db")


missing_repos = repo_missing_in_db()
add_repo_to_db(missing_repos)

