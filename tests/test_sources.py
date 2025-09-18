from __future__ import annotations

import unittest

from budget_app import create_app, db


class SourceRoutesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "SQLALCHEMY_ENGINE_OPTIONS": {"connect_args": {"check_same_thread": False}},
            }
        )
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_duplicate_source_creation_returns_conflict(self) -> None:
        payload = {"name": "Maaş", "type": "salary"}
        first_response = self.client.post("/sources", json=payload)
        self.assertEqual(first_response.status_code, 201)

        duplicate_response = self.client.post("/sources", json=payload)
        self.assertEqual(duplicate_response.status_code, 409)
        self.assertEqual(
            duplicate_response.get_json(),
            {"error": "Bu isimde bir kaynak zaten mevcut"},
        )

    def test_duplicate_source_rename_returns_conflict(self) -> None:
        first = self.client.post("/sources", json={"name": "Ana hesap", "type": "bank"})
        second = self.client.post("/sources", json={"name": "Yedek hesap", "type": "cash"})
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)

        second_id = second.get_json()["id"]
        rename_response = self.client.put(
            f"/sources/{second_id}",
            json={"name": "Ana hesap"},
        )
        self.assertEqual(rename_response.status_code, 409)
        self.assertEqual(
            rename_response.get_json(),
            {"error": "Bu isimde bir kaynak zaten mevcut"},
        )


if __name__ == "__main__":
    unittest.main()
