"""
Known-answer tests for the Dahua password hashing.

Vectors were captured from the original upstream code before any changes, so these tests prove the
modernisation did not alter protocol behaviour. 'admin' -> '6QNMIQGe' is the widely published Dahua
gen1 hash of 'admin'.
"""
import pytest

from dahua_logon_modes import (
    DECRYPT,
    ENCRYPT,
    dahua_digest_md5_hash,
    dahua_dvrip_md5_hash,
    dahua_gen0_hash,
    dahua_gen1_hash,
    dahua_gen2_md5_hash,
    dahua_logon,
    dahua_onvif_sha1_hash,
)


@pytest.mark.parametrize(
    "password, expected",
    [
        ("admin", "6QNMIQGe"),
        ("password", "mF95aD4o"),
        ("123456", "nTBCS19C"),
        ("Tr1cky!Pa55", "3LUWUmPn"),
    ],
)
def test_gen1_hash(password, expected):
    assert dahua_gen1_hash(password) == expected


def test_gen2_md5_hash():
    assert dahua_gen2_md5_hash(
        dh_random="1234567890", dh_realm="Login to ABCD", username="admin", password="admin"
    ) == "3DF03DBC9409480CF69E6EC80E7A231B"


def test_gen2_md5_hash_return_hash():
    assert dahua_gen2_md5_hash(
        dh_random="x", dh_realm="Login to ABCD", username="admin", password="admin", return_hash=True
    ) == "FFE4CCE0594BC82A4B3554D6D36D520A"


def test_gen2_saved_host_matches_password():
    stored = dahua_gen2_md5_hash(
        dh_random="x", dh_realm="Login to ABCD", username="admin", password="admin", return_hash=True
    )
    saved_host = {"password": {"gen2": stored}}
    assert dahua_gen2_md5_hash(
        dh_random="1234567890", dh_realm="Login to ABCD", username="admin", saved_host=saved_host
    ) == "3DF03DBC9409480CF69E6EC80E7A231B"


def test_digest_md5_hash():
    assert dahua_digest_md5_hash(
        dh_random="abc", dh_realm="Login to ABCD", username="admin", password="admin",
        created="2026-01-01T00:00:00Z",
    ) == "270c8df0386b7a0e14ee794bc6068db8"


def test_dvrip_md5_hash_saved_host():
    saved_host = {"password": {"gen1": dahua_gen1_hash("admin")}}
    assert dahua_dvrip_md5_hash(
        dh_random="9876", username="admin", saved_host=saved_host
    ) == "E18B33EA51E4F8F0730DD82BB1D4655B"


def test_dvrip_md5_hash_password_matches_saved_host():
    """
    Regression test: upstream's conditional expression bound loosest, so supplying a password hashed only
    gen1(password) (giving 40AF6DF1...) instead of 'username:random:gen1'. Both paths must now agree.
    """
    saved_host = {"password": {"gen1": dahua_gen1_hash("admin")}}
    from_password = dahua_dvrip_md5_hash(dh_random="9876", username="admin", password="admin")
    from_saved = dahua_dvrip_md5_hash(dh_random="9876", username="admin", saved_host=saved_host)
    assert from_password == from_saved == "E18B33EA51E4F8F0730DD82BB1D4655B"


@pytest.mark.parametrize(
    "plain, cipher_hex",
    [
        ("admin", "c4a3af489956b6b4"),
        ("888888", "7b22257a191433e9"),
        ("abc", "920968bea6855376"),
    ],
)
def test_gen0_3des(plain, cipher_hex):
    cipher = dahua_gen0_hash(plain, ENCRYPT)
    assert cipher.hex() == cipher_hex
    assert dahua_gen0_hash(cipher, DECRYPT) == plain


def test_onvif_sha1_hash_shape():
    result = dahua_onvif_sha1_hash(password="admin")
    assert set(result) == {"authorityInfo", "password", "random"}


def test_wsse_created_timestamp_format():
    """utcnow() was replaced; the WSSE 'created' value must keep the exact YYYY-MM-DDTHH:MM:SSZ form."""
    import re

    query_args = {"params": {"random": "1234567890", "realm": "Login to ABCD", "encryption": "Default"}}
    params = dahua_logon(logon="wsse", query_args=query_args, username="admin", password="admin")
    assert params["passwordType"] == "WSSE"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", params["authorityInfo"])
