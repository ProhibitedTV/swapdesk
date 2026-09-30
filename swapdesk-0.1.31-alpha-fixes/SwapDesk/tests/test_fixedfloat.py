import unittest
from decimal import Decimal

from providers.fixedfloat import FixedFloat


class FixedFloatQuoteResponseTests(unittest.TestCase):
    @staticmethod
    def _provider(response):
        provider = FixedFloat(api_key="test-key", api_secret="test-secret")
        provider._signed_obj = lambda *args, **kwargs: response
        return provider

    def test_quote_rejects_malformed_errors_field(self):
        for errors in ({"code": "LIMIT_MIN"}, [{"code": "LIMIT_MIN"}]):
            with self.subTest(errors=errors):
                quote = self._provider({"errors": errors}).get_quote(
                    "BTC", "XMR", Decimal("1")
                )

                self.assertFalse(quote.ok)
                self.assertIn("malformed errors", quote.error)

    def test_quote_rejects_malformed_currency_legs(self):
        responses = (
            {"from": "not-an-object", "to": {"amount": "2"}},
            {"from": {"min": "0.1"}, "to": ["not-an-object"]},
            {"from": None, "to": {"amount": "2"}},
        )
        for response in responses:
            with self.subTest(response=response):
                quote = self._provider(response).get_quote(
                    "BTC", "XMR", Decimal("1")
                )

                self.assertFalse(quote.ok)
                self.assertIn("malformed currency legs", quote.error)

    def test_quote_rejects_missing_non_numeric_and_non_positive_receive_amount(self):
        for value in (None, "not-a-number", "0", "-1"):
            with self.subTest(receive_amount=value):
                quote = self._provider({
                    "from": {"min": "0.1", "max": "10"},
                    "to": {"amount": value},
                }).get_quote("BTC", "XMR", Decimal("1"))

                self.assertFalse(quote.ok)
                self.assertIn("invalid receive amount", quote.error)

    def test_valid_quote_preserves_limits_and_rate(self):
        quote = self._provider({
            "from": {"min": "0.1", "max": "10"},
            "to": {"amount": "2.5"},
        }).get_quote("BTC", "XMR", Decimal("1"))

        self.assertTrue(quote.ok)
        self.assertEqual(quote.estimated_receive, Decimal("2.5"))
        self.assertEqual(quote.rate, Decimal("2.5"))
        self.assertEqual(quote.min_amount, Decimal("0.1"))
        self.assertEqual(quote.max_amount, Decimal("10"))


if __name__ == "__main__":
    unittest.main()
