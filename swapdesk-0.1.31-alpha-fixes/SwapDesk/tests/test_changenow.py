import unittest
from decimal import Decimal

from providers.changenow import ChangeNow


class ChangeNowQuoteResponseTests(unittest.TestCase):
    @staticmethod
    def _provider(response):
        provider = ChangeNow(api_key="test-key")
        provider._get = lambda *args, **kwargs: response
        return provider

    def test_quote_rejects_non_object_estimate_response(self):
        quote = self._provider([]).get_quote("BTC", "XMR", Decimal("1"))

        self.assertFalse(quote.ok)
        self.assertIn("expected a JSON object", quote.error)

    def test_quote_rejects_missing_non_numeric_and_non_positive_to_amount(self):
        provider = ChangeNow(api_key="test-key")
        for value in (None, "not-a-number", "0", "-1"):
            with self.subTest(to_amount=value):
                provider._get = lambda *args, _value=value, **kwargs: {
                    "toAmount": _value,
                }
                quote = provider.get_quote("BTC", "XMR", Decimal("1"))

                self.assertFalse(quote.ok)
                self.assertIn("invalid toAmount", quote.error)

    def test_valid_quote_preserves_best_effort_minimum(self):
        provider = ChangeNow(api_key="test-key")

        def fake_get(url, **kwargs):
            if url.endswith("/exchange/min-amount"):
                return {"minAmount": "0.1"}
            return {"toAmount": "2"}

        provider._get = fake_get
        quote = provider.get_quote("BTC", "XMR", Decimal("1"))

        self.assertTrue(quote.ok)
        self.assertEqual(quote.estimated_receive, Decimal("2"))
        self.assertEqual(quote.rate, Decimal("2"))
        self.assertEqual(quote.min_amount, Decimal("0.1"))

    def test_malformed_minimum_response_does_not_break_valid_quote(self):
        provider = ChangeNow(api_key="test-key")

        def fake_get(url, **kwargs):
            if url.endswith("/exchange/min-amount"):
                return []
            return {"toAmount": "2"}

        provider._get = fake_get
        quote = provider.get_quote("BTC", "XMR", Decimal("1"))

        self.assertTrue(quote.ok)
        self.assertIsNone(quote.min_amount)


if __name__ == "__main__":
    unittest.main()
