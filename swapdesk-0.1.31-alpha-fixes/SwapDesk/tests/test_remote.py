import unittest
from decimal import Decimal

from providers import ProviderError, STATUS_UNKNOWN
from remote import RemoteSwapDesk


class RemoteResponseShapeTests(unittest.TestCase):
    @staticmethod
    def _provider(response):
        provider = RemoteSwapDesk("https://example.invalid", "test-key")
        provider._call = lambda method, path, payload=None: response
        return provider

    @staticmethod
    def _auth_provider(response):
        provider = RemoteSwapDesk("https://example.invalid", "test-key")
        provider._post = lambda *args, **kwargs: response
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

    def test_auth_rejects_non_string_and_whitespace_tokens(self):
        for token in (["token"], "bad token"):
            with self.subTest(token=token):
                provider = self._auth_provider({
                    "session_token": token,
                    "expires_at": 123,
                })
                with self.assertRaisesRegex(ProviderError, "invalid session token"):
                    provider._auth_token()

    def test_auth_rejects_malformed_expiry(self):
        for expiry in ("not-an-int", True, -1, []):
            with self.subTest(expiry=expiry):
                provider = self._auth_provider({
                    "session_token": "token-123",
                    "expires_at": expiry,
                })
                with self.assertRaisesRegex(ProviderError, "invalid session expiry"):
                    provider._auth_token()

    def test_auth_accepts_printable_token_and_integer_string_expiry(self):
        provider = self._auth_provider({
            "session_token": " token-123 ",
            "expires_at": "1234567890",
        })

        token = provider._auth_token()

        self.assertEqual(token, "token-123")
        self.assertEqual(provider._token, "token-123")
        self.assertEqual(provider._token_expires_at, 1234567890)

    def test_auth_allows_missing_expiry_without_crashing(self):
        provider = self._auth_provider({"session_token": "token-123"})

        self.assertEqual(provider._auth_token(), "token-123")
        self.assertEqual(provider._token_expires_at, 0)


if __name__ == "__main__":
    unittest.main()
