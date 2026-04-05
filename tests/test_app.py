import unittest
from unittest.mock import MagicMock, patch

import app as app_module


class TestHomePage(unittest.TestCase):
    def setUp(self) -> None:
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    @patch.object(app_module, "load_repos_for_home")
    def test_home_renders_repo_cards(self, mock_load: MagicMock) -> None:
        mock_load.return_value = [
            {
                "name": "demo",
                "description": "Test repo",
                "language": "Python",
                "stars": 7,
                "url": "https://github.com/u/demo",
            },
        ]

        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("GHdotcom", html)
        self.assertIn("demo", html)
        self.assertIn("Python", html)
        self.assertIn("github.com/u/demo", html)
        self.assertIn("repo-slide", html)
        self.assertIn("data-repo-slide", html)
        mock_load.assert_called_once()

    @patch.object(app_module, "load_repos_for_home")
    def test_home_empty_repos(self, mock_load: MagicMock) -> None:
        mock_load.return_value = []

        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("Aún no hay repositorios", html)

    @patch.object(app_module, "load_repos_for_home")
    def test_home_db_failure_returns_503(self, mock_load: MagicMock) -> None:
        mock_load.side_effect = ConnectionError("db down")

        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 503)
        html = resp.data.decode("utf-8")
        self.assertIn("Comprobá", html)


if __name__ == "__main__":
    unittest.main()
