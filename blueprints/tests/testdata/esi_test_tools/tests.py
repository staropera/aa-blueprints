from datetime import datetime

from bravado.exception import HTTPNotFound
from django.test import TestCase

from .main import EsiClientStub, EsiEndpoint

testdata = {
    "Alpha": {
        "get_cake": {"1": "cheesecake", "2": "strawberrycake"},
        "get_details": {"1": {"appointment": "2015-03-24T11:37:00Z"}},
        "get_secret": {"1": "blue secret", "2": "red secret"},
        "get_simple": "steak",
        "get_double_impact": {"1": {"A": "Madrid", "B": "Tokyo"}},
    }
}


class TestEsiClientStub(TestCase):
    def setUp(self) -> None:
        self.stub = EsiClientStub(
            testdata,
            [
                EsiEndpoint("Alpha", "get_cake", "cake_id"),
                EsiEndpoint("Alpha", "get_secret", "secret_id", needs_token=True),
                EsiEndpoint("Alpha", "get_simple"),
                EsiEndpoint("Alpha", "get_double_impact", ("first_id", "second_id")),
            ],
        )

    def test_can_create_endpoint(self):
        self.assertTrue(hasattr(self.stub, "Alpha"))
        self.assertTrue(hasattr(self.stub.Alpha, "get_cake"))
        self.assertEqual(self.stub.Alpha.get_cake(cake_id=1).results(), "cheesecake")
        self.assertEqual(
            self.stub.Alpha.get_cake(cake_id=2).results(), "strawberrycake"
        )
        self.assertEqual(self.stub.Alpha.get_simple().results(), "steak")
        self.assertEqual(
            self.stub.Alpha.get_double_impact(first_id="1", second_id="B").results(),
            "Tokyo",
        )

    def test_raises_exception_on_wrong_pk(self):
        with self.assertRaises(ValueError):
            self.stub.Alpha.get_cake(fruit_id=1).results()

    def test_raises_exception_on_missing_pk(self):
        with self.assertRaises(ValueError):
            self.stub.Alpha.get_cake().results()

    def test_raises_exception_on_missing_data(self):
        with self.assertRaises(HTTPNotFound):
            self.stub.Alpha.get_cake(cake_id=3).results()

    def test_raises_exception_on_missing_token_if_required(self):
        with self.assertRaises(ValueError):
            self.stub.Alpha.get_secret(secret_id=1).results()

    def test_raises_exception_when_trying_to_refine_same_endpoint(self):
        with self.assertRaises(ValueError):
            EsiClientStub(
                testdata,
                [
                    EsiEndpoint("Alpha", "get_cake", "cake_id"),
                    EsiEndpoint("Alpha", "get_cake", "cake_id"),
                ],
            )

    def test_raises_exception_when_trying_to_refine_endpoint_without_data(self):
        with self.assertRaises(ValueError):
            EsiClientStub(
                testdata,
                [
                    EsiEndpoint("Alpha", "get_fruit_id", "fruit_id"),
                ],
            )

    def test_can_convert_datetimes(self):
        stub = EsiClientStub(
            testdata,
            [
                EsiEndpoint("Alpha", "get_details", "id"),
            ],
        )
        results = stub.Alpha.get_details(id=1).results()
        self.assertIsInstance(results["appointment"], datetime)
