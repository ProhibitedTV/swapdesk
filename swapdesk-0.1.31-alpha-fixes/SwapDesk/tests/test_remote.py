import unittest
from decimal import Decimal

from providers import STATUS_UNKNOWN
from remote import RemoteSwapDesk


class RemoteResponseShapeTests(unittest.TestCase):
    @staticmethod
    def _provider(response):
        provider = RemoteSwapDesk("https://example.invalid", "test-key")
        provider._call = lambda method, path, payload=None: response
        return provider

    def test_quote_rejects_non_object_response(self):
        quote = self._provider([]).get_quote("BTC", "XMR", Decimal("1"))

        self.assertFalse(quote.ok)
        self.assertIn("expected a JSON object", quote.error)

    def test_quote_rejects_non_list_quotes_field(self):
        quote = self._provider({"quotes": {"quote_id": "q1"}}).get_quote(
            "BTC", "XMR", Decimal("1")
        )

        self.assertFalse(quote.ok)
        self.assertIn("non-list 'quotes'", quote.error)

    def test_quote_rejects_non_object_quote_entry(self):
        quote = self._provider({"quotes": ["not-an-object"]}).get_quote(
            "BTC", "XMR", Decimal("1")
        )

        self.assertFalse(quote.ok)
        self.assertIn("quote entry of type str", quote.error)

    def test_malformed_error_entries_do_not_escape(self):
        quote = self._provider({"quotes": [], "errors": ["broken"]}).get_quote(
            "BTC", "XMR", Decimal("1")
        )

        self.assertFalse(quote.ok)
        self.assertFalse(quote.unsupported)
        self.assertIn("1 provider(s) failed", quote.error)

    def test_quote_requires_usable_quote_id(self):
        quote = self._provider(
            {"quotes": [{"receive_amount": "2", "rate": "2"}]}
        ).get_quote("BTC", "XMR", Decimal("1"))

        self.assertFalse(quote.ok)
        self.assertIn("no usable quote id", quote.error)

    def test_quote_rejects_non_positive_receive_amount(self):
        quote = self._provider(
            {"quotes": [{
                "quote_id": "q1",
                "receive_amount": "-1",
                "rate": "1",
            }]}
        ).get_quote("BTC", "XMR", Decimal("1"))

        self.assertFalse(quote.ok)
        self.assertIn("invalid receive amount", quote.error)

    def test_quote_rejects_non_positive_rate(self):
        quote = self._provider(
            {"quotes": [{
                "quote_id": "q1",
                "receive_amount": "1",
                "rate": "0",
            }]}
        ).get_quote("BTC", "XMR", Decimal("1"))

        self.assertFalse(quote.ok)
        self.assertIn("invalid rate", quote.error)

    def test_valid_quote_is_cached_and_non_string_via_is_ignored(self):
        provider = self._provider(
            {"quotes": [{
                "quote_id": " q-123 ",
                "receive_amount": "2",
                "rate": "2",
                "provider": 123,
                "via": [],
            }]}
        )

        quote = provider.get_quote("BTC", "XMR", Decimal("1"))

        self.assertTrue(quote.ok)
        self.assertEqual(quote.via, None)
        self.assertEqual(provider._quote_ids[("BTC", "XMR", "1")], "q-123")

    def test_status_non_object_response_fails_safe(self):
        provider = self._provider([])

        self.assertEqual(provider.get_status("order-1"), STATUS_UNKNOWN)

    def test_status_non_string_value_fails_safe(self):
        provider = self._provider({"status": ["Complete"]})

        self.assertEqual(provider.get_status("order-1"), STATUS_UNKNOWN)


if __name__ == "__main__":
    unittest.main()
