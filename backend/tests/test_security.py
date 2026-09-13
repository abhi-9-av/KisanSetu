"""Focused security regression tests for the local backend hardening."""

import base64
import hashlib
import hmac
import json
import time
import unittest

from fastapi.security import HTTPAuthorizationCredentials

from backend import auth
from backend.config import get_settings
from backend.main import current_farmer, development_operator_access


class SecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        auth.reset_rate_limits()

    def test_signed_token_rejects_invalid_and_expired_tokens(self) -> None:
        token = auth.create_session("F-test")
        self.assertEqual(auth.farmer_id_for_token(token), "F-test")
        self.assertIsNone(auth.farmer_id_for_token(token + "x"))

        header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
        payload = base64.urlsafe_b64encode(
            json.dumps({"sub": "F-test", "exp": int(time.time()) - 1}).encode()
        ).rstrip(b"=").decode()
        unsigned = f"{header}.{payload}"
        signature = hmac.new(
            get_settings().auth_secret_key.encode(), unsigned.encode(), hashlib.sha256
        ).digest()
        expired = f"{unsigned}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"
        self.assertIsNone(auth.farmer_id_for_token(expired))

    def test_operator_credential_is_constant_time_checked(self) -> None:
        self.assertTrue(development_operator_access(get_settings().operator_access_token))
        with self.assertRaises(Exception) as context:
            development_operator_access("wrong")
        self.assertEqual(context.exception.status_code, 401)

    def test_rate_limit(self) -> None:
        self.assertTrue(auth.check_rate_limit("request", "test", limit=1))
        self.assertFalse(auth.check_rate_limit("request", "test", limit=1))

    def test_protected_endpoint_rejects_missing_or_invalid_bearer(self) -> None:
        with self.assertRaises(Exception) as missing:
            current_farmer(None, object())
        self.assertEqual(missing.exception.status_code, 401)
        with self.assertRaises(Exception) as invalid:
            current_farmer(HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-token"), object())
        self.assertEqual(invalid.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
