import unittest
from decimal import Decimal

from providers.sideshift import SideShift


class SideShiftQuoteResponseTests(unittest.TestCase):
    @staticmethod
    def _provider(response):
        provider = SideShift()
        provider._get = lambda *args, **kwargs: response
        return provider

    def test_quote_rejects_non_object_response(self):
        quote = self._provider([]).get_quote("BTC", "XMR", Decimal("1"))

        self.assertFalse(quote.ok)
        self.assertIn("expected a JSON object", quote.error)

    def test_quote_rejects_non_positive_rate(self):
        quote = self._provider({
            "rate": "0",
            "settleAmount": "1",
        }).get_quote("BTC", "XMR", Decimal("1"))

        self.assertFalse(quote.ok)
        self.assertIn("non-positive rate", quote.error)

    def test_quote_rejects_non_positive_receive_estimate(self):
        quote = self._provider({
            "rate": "1",
            "settleAmount": "0",
        }).get_quote("BTC", "XMR", Decimal("1"))

        self.assertFalse(quote.ok)
        self.assertIn("no usable receive estimate", quote.error)

    def test_quote_rejects_missing_numeric_values(self):
        quote = self._provider({
            "rate": "not-a-number",
            "settleAmount": "also-not-a-number",
        }).get_quote("BTC", "XMR", Decimal("1"))

        self.assertFalse(quote.ok)
        self.assertIn("no usable receive estimate", quote.error)

    def test_quote_derives_receive_estimate_from_positive_rate(self):
        quote = self._provider({
            "rate": "2",
            "min": "0.1",
            "max": "10",
        }).get_quote("BTC", "XMR", Decimal("1.5"))

        self.assertTrue(quote.ok)
        self.assertEqual(quote.estimated_receive, Decimal("3.0"))
        self.assertEqual(quote.rate, Decimal("2"))
        self.assertEqual(quote.min_amount, Decimal("0.1"))
        self.assertEqual(quote.max_amount, Decimal("10"))


if __name__ == "__main__":
    unittest.main()
